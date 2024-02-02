from ast import List
from fprime_gds.common.pipeline.standard import StandardPipeline
from fprime_gds.common.utils.config_manager import ConfigManager
from fprime_gds.common.history.chrono import ChronologicalHistory

from fprime_gds.common.templates.ch_template import ChTemplate

from fprime_gds.executables.cli import ParserBase, StandardPipelineParser, OpenMCTTelemetryPollerParser
from typing import Any, Dict, Tuple

from fprime_openmct.fprime_to_openmct import TopologyAppDictionaryJSONifier 

import requests 
import time 

import json



class TelemPipeline(StandardPipeline):
    """
    The Telemetry Pipeline class inherits from the F-Prime GDS Standard Pipeline Object for Telemetry Polling.
    It includes the following data members:

    1. StandardPipeline member variables -> Includes Dictionaries, Coders, Object History, Filing, and Transport Info
    2. telem_chron_hist -> Chronological History Object that will request new telemetry
    3. telem_hist -> List where raw telemetry objects requested by telem_chron_hist will be stored
    4. telem_data -> Contains list of processed telemetry objects in the format that OpenMCT will accept
    5. telem_init_states -> Contains dictionary of telemetry object names and their immediate value. Used to initialize values and define the telemetry states to be processed by OpenMCT server 
    6. telem_init_json -> Contains JSON of telemetry object names and their value. Saved in OpenMCT directory and used by OpenMCT server to define initial telemetry states.
    7. max_state_count -> Used to keep count of the largest number telemetry objects recieved by the pipeline in a single telemetry request
    8. json_writeable -> Used to determine if heli_states contains telemetry information. If true, the data can be written to a JSON that OpenMCT will accept
    """
    def __init__(self, connection_ip="127.0.0.1", connection_port=50050, dict_path="", log_path=""):
        StandardPipeline.__init__(self)
        self.setup(ConfigManager(), dict_path, log_path)
        self.connect(connection_ip, connection_port)
        self.telem_chron_hist = ChronologicalHistory()
        self.coders.register_channel_consumer(self.telem_chron_hist)
        self.telem_hist:List[ChTemplate] = []
        self.telem_data = []
        self.telem_init_states = {}
        self.telem_init_json = {}
        self.max_state_count = 0
        self.json_writeable = False
        self.topologyToJson: TopologyAppDictionaryJSONifier = TopologyAppDictionaryJSONifier(dict_path)

    def get_telem_hist(self):
        return self.telem_hist

    def update_telem_hist(self):
        self.telem_hist = self.telem_chron_hist.retrieve_new()
        #print(self.telem_hist)
        if (len(self.telem_hist) > self.max_state_count):
            self.max_state_count = len(self.telem_hist)

    def set_telem_json(self):
        self.telem_data = []
        for channel in self.telem_hist:

            full_channel_name = channel.template.get_full_name().replace(".", "_")
            channel_structure = self.topologyToJson.dictionary_of_channel[full_channel_name]
            data = channel.get_val()
            for single_telemetry in channel_structure:
                keys = single_telemetry.get("keys", [])
                value = data
                for key in keys:
                    value = value[key]
                self.json_writeable = True

                hist_name = full_channel_name+(('_'+'_'.join(map(str, keys))) if len(keys)>0 else "")
                hist_data = {
                            'name': hist_name, 
                            'data': {
                                    'id':hist_name,
                                    'val':value,
                                    'time':channel.time.to_readable()
                                    }
                            }
                
                self.telem_data.append(hist_data)

                if self.json_writeable:
                    self.telem_init_states[hist_name] = value




    def write_telem_json(self, fname="openmct/initial_states.json"):
        self.telem_init_json = json.dumps(self.telem_init_states, indent=4)
        #print(len(self.telem_init_states))
        with open(fname, "w") as outfile:
            outfile.write(self.telem_init_json)

    def post_telem(self, uri="http://127.0.0.1:4052/fprime_telem"):
        requests.post(uri, json={'name': 'heli', 'telem': self.telem_data}) 

def main():
    #Set up and Process Command Line Arguments
    arguments, _ = ParserBase.parse_args([StandardPipelineParser, OpenMCTTelemetryPollerParser],
                                                description="OpenMCT Telemetry Polling Parser",
                                                client=True  # This is a client script, thus client=True must be specified
                                                )

    # instantiate the GDS and connect to the Deployment
    telem_pipeline = TelemPipeline(connection_ip=arguments.tts_addr, 
                                connection_port=arguments.tts_port,
                                dict_path=arguments.dictionary,
                                log_path=arguments.logs)
    
    # Continuously poll for telemetry from the F-Prime GDS Pipeline
    while True:
        #Poll the F-Prime GDS Pipeline for telemetry, and update the latest telemetry JSON
        telem_pipeline.update_telem_hist() 
        telem_pipeline.set_telem_json()
        
        #Post Telemetry Information to the server address OpenMCT is listening on
        telem_pipeline.post_telem(arguments.openmct_uri)

        #Sleep at user defined rate 
        time.sleep(1/arguments.openmct_telem_rate)

if __name__ == '__main__':
    main()