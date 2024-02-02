# fprime-openmct
Scripts to connect the F Prime ground system to OpenMCT

## Installation Instructions.
OpenMCT runs a server using Node JS, so Node must be installed. Node Version 18.17.0 works and is stable with OpenMCT.
### Install NVM (Node Version Manager)
```
curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.39.1/install.sh | bash
```
### Install Node 
```
nvm install v18.17.0
nvm alias default v18.17.0 # Make v18.17.0 default if you have multiple Node Versions on your system
```

### Install fprime-openmct as a pip package
```
git clone https://github.com/mohitsingh999/fprime-openmct --recurse-submodules # Currently being reviewed in a pull request. Link will be updated to the f-prime community OpenMCT when made available.
pip install . # from the root of the repository 
```


### Install F-Prime OpenMCT Dependencies and OpenMCT from Source
Not required if pip install is done.

```
fprime-openmct-setup # from the root of the repository
```
This command should install the OpenMCT Server and the F-Prime to OpenMCT pipeline in Node JS. 


The scripts generating the OpenMCT JSON Definitions and polling for real time telemetry use the latest F-Prime GDS API, so it is key to install the latest versions of `fprime_gds` and `fprime_tools`. 
### Install F-Prime GDS(>3.2.0) and F-Prime Tools(>3.2.0)
```
pip install fprime_gds==3.2.0 fprime_tools==3.2.0
```



## Running the F-Prime OpenMCT Pipeline

### Method 1: Manually Running without updated F' GDS

#### Generating the OpenMCT JSON and Initial States
```
cd telem_definition_generator
python fprime_to_openmct.py --dictionary {path to F-Prime Topology App Dictionary XML}
```

There should now be files called `initial_states.json` and `FPrimeDeploymentTopologyAppDictionary.json` in the root of the repository. 

#### Starting the OpenMCT Server
```
cd src/fprime_openmct/javascript
npm start
```
This command starts up the OpenMCT server with the Telemetry Definitions generated in `FPrimeDeploymentTopologyAppDictionary.json`. Using `initial_states.json`, the server gets initial values for each of the telemetry channels. For real-time telemetry, we must run another script that polls the F-Prime GDS API for telemetry from an F-Prime deployment. 

#### Subscribing and Publishing FPrime Telemetry via F-Prime GDS 
To poll for realtime telemetry, we must run `fprime_telem_poller.py`. 
```
cd src/fprime_openmct 
python fprime_telem_poller.py --dictionary {path to F-Prime Topology App Dictionary XML} 
```
Going to `localhost:8080` on a browser will show the F-Prime Telemetry Channels registered in the framework, outputting real time telemetry recieved. 

For additional details on running the tool with the standard `Ref` deployment, see `RefTutorial.md`. 

### Method 2: Running with updated F-Prime GDS
An updated fork of F-Prime GDS allows users to merely run one command to generate the OpenMCT JSON and Initial States, Start the OpenMCT Server, and Subscribe and Publish FPrime Telemetry.
```
fprime-gds --openmct
```
This fork is currently available at https://github.com/mohitsingh999/fprime-gds and is currently being reviewed in a pull request to the standard F-Prime GDS repository. It can be cloned and installed as a pip package with the command ```pip install .```





