import xml.etree.ElementTree as ET

from fprime_gds.common.pipeline.dictionaries import Dictionaries
from fprime_gds.executables.cli import ParserBase, StandardPipelineParser
import json
import fprime_openmct

from fprime.common.models.serialize.array_type import ArrayType
from fprime.common.models.serialize.bool_type import BoolType
from fprime.common.models.serialize.enum_type import EnumType
from fprime.common.models.serialize.numerical_types import (
    I8Type,
    I16Type,
    I32Type,
    I64Type,
    U8Type,
    U16Type,
    U32Type,
    U64Type,
    F32Type,
    F64Type,
)
from fprime.common.models.serialize.serializable_type import SerializableType
from fprime.common.models.serialize.string_type import StringType

class TopologyAppDictionaryJSONifier():
    """
    The Topology App Dictionary JSONifier class takes a python dictionary of F-Prime Telemetry Definitions and Converts it to the OpenMCT Definition
    It includes the following data members:

    1. int_type_list -> List of F-Prime Int Types
    2. float_type-list -> List of F-Prime Float Types
    3. framework_list -> List of F-Prime Framework Strings
    4. measurement_list -> List of F-Prime Telemetry Measurements
    5. dict_enum -> F-Prime Dictionary for F-Prime Enum Definitions
    6. dict_test -> F-Prime Dictionary for F-Prime Commands, Events, Telem Channels, and Parameters
    7. channel_list -> List of F-Prime Telemetry Channel Definitions
    8. openmct_telem_dict -> OpenMCT-formatted Dictionary of F-Prime Telemetry Channel Information

    """
    def __init__(self, xml_path='MPPTDeploymentTopologyAppDictionary.xml'):
        project_dictionary = Dictionaries()
        project_dictionary.load_dictionaries(xml_path, packet_spec=None)
        
        self.dictionary_of_channel = {}

        for key, value in project_dictionary.channel_id.items():
            channel_name = value.get_full_name().replace(".", "_")

            keys_to_access_values_and_type = []
            self.create_access_list(
                value.get_type_obj(), keys_to_access_values_and_type
            )
            self.dictionary_of_channel[channel_name] = keys_to_access_values_and_type

        self.__measurement_list = []
        self.__init_states = {}

        #Populate the measurement list  
        self.loadEntries()

        self.__openmct_telem_dict = {}
        self.__openmct_telem_dict['name'] = xml_path.replace('.xml', '')
        self.__openmct_telem_dict['key'] = xml_path.replace('.xml', '')
        self.__openmct_telem_dict['measurements'] = self.__measurement_list

    # Load Telemetry Channel List and format it to be in the OpenMCT Dictionary Format
    def loadEntries(self):

        for chanel_name, keys_to_access_values_and_type in self.dictionary_of_channel.items():
            
            for channel_member in self.dictionary_of_channel[chanel_name]:
                measurement_entry = {}
                measurement_entry['values'] = [{}, {}]
                keys = channel_member.get("keys", [])
                measurement_entry['name'] = chanel_name+(('_'+'_'.join(map(str, keys))) if len(keys)>0 else "")
                measurement_entry['key'] = chanel_name+(('_'+'_'.join(map(str, keys))) if len(keys)>0 else "")

                measurement_entry['values'][0]['key'] = "value" #channel_obj.id
                measurement_entry['values'][0]['name'] = "Value" #channel_obj.name
                measurement_entry['values'][0]['hints'] = {}
                measurement_entry['values'][0]['hints']['range'] = 1

                measurement_entry['values'][1]['key'] = 'utc'
                measurement_entry['values'][1]['source'] = 'timestamp'
                measurement_entry['values'][1]['name'] = 'Timestamp'
                measurement_entry['values'][1]['format'] = 'utc'
                measurement_entry['values'][1]['hints'] = {}
                measurement_entry['values'][1]['hints']['domain'] = 1

                type_i = channel_member.get("type", [])
                measurement_entry['values'][0]['format'] = type_i

                if(type_i == "float"):
                    self.__init_states[measurement_entry['key']] = 0.0
                elif(type_i == "integer"):
                    measurement_entry['values'][0]['format'] = 'integer'
                    self.__init_states[measurement_entry['key']] = 0 
                elif(type_i == 'enum'):
                    measurement_entry['values'][0]['enumerations'] = [{'string': key, 'value': value} for key, value in channel_member.get("enum", {}).items()]
                    self.__init_states[measurement_entry['key']] = list(channel_member.get("enum", {}).keys())[0]

                self.__measurement_list.append(measurement_entry)   

        self.__init_states = {**self.__init_states}#, **self.__dict_xml._init_serializables}

    #Write OpenMCT dictionary to a JSON file
    def writeOpenMCTJSON(self, fname, fpath=fprime_openmct.__file__.replace('__init__.py', 'javascript')):
        openmct_json = json.dumps(self.__openmct_telem_dict, indent=4)
        with open(fpath + '/' + fname + ".json", "w") as outfile:
            outfile.write(openmct_json)

    def writeInitialStatesJSON(self, fname, fpath=fprime_openmct.__file__.replace('__init__.py', 'javascript')):
        initialstates_json = json.dumps(self.__init_states, indent=4)
        with open(fpath + '/' + fname + ".json", "w") as outfile:
            outfile.write(initialstates_json)    

    def create_access_list(self, ch_type, keysArr_types=[], keys_until_now=[]):
        """
        It recursively create a list of dictionaries where each dictionary contains for each primary type of a channel:
        * a list of keys to access a primary type
        ****
        """
        channel_types = {
            F32Type: 'float',
            F64Type: 'float',
            I8Type: 'integer',
            I16Type: 'integer',
            I32Type: 'integer',
            I64Type: 'integer',
            U8Type: 'integer',
            U16Type: 'integer',
            U32Type: 'integer',
            U64Type: 'integer',
            BoolType: 'integer'
        }

        if ch_type in channel_types:
            channel_type = channel_types[ch_type]
            keysArr_types.append({"keys":keys_until_now, "type": channel_type})
            return
        elif(issubclass(ch_type, ArrayType)):
            for index in  range(0, ch_type.LENGTH):
                # Call recursively to deserialize the channel element
                upgrade_key_list= (keys_until_now+[index]).copy()
                self.create_access_list(ch_type.MEMBER_TYPE, keysArr_types, upgrade_key_list)
        elif(issubclass(ch_type, EnumType)):
            keysArr_types.append({"keys":keys_until_now, "type": "enum", "enum":ch_type.ENUM_DICT})
            return
        elif(issubclass(ch_type, StringType)):
            keysArr_types.append({"keys":keys_until_now, "type": "text"})
            return
        elif(issubclass(ch_type, SerializableType)):
            for member_name, member_value, member_format, member_desc in ch_type.MEMBER_LIST:
                # Call recursively to deserialize the channel element
                upgrade_key_list= (keys_until_now+[member_name]).copy()
                self.create_access_list(member_value, keysArr_types, upgrade_key_list)
                
        else:
            raise Exception("Not supported type") 

if __name__ == '__main__':
    #Set up and Process Command Line Arguments
    arguments, _ = ParserBase.parse_args([StandardPipelineParser],
                                                description="Topology App Dictionary XML to OpenMCT JSON Parser",
                                                client=True  # This is a client script, thus client=True must be specified
                                                )

    #Convert Topology App Dictionary XML file to an OpenMCT JSON 
    top_dict = TopologyAppDictionaryJSONifier(arguments.dictionary)
    top_dict.writeOpenMCTJSON('FPrimeDeploymentTopologyAppDictionary', 'javascript/')
    top_dict.writeInitialStatesJSON('initial_states', 'javascript/')

