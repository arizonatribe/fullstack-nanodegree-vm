# Udacity FullStack Project
This project consists of code used by several courses in the Full Stack Web Developer
 nanodegree. One course uses the `restaurants` folder, another the `tournament` folder, etc.
 Each folder contains its own readme covering its functionality. Please view the the file
 in each folder for full descriptions of each course project contained therein.

### Project dependencies
* Vagrant
* VirtualBox

#### VirtualBox
To run this project, you will need to have VirtualBox installed, which can be
downloaded [here](https://www.virtualbox.org/wiki/Downloads) and installed onto
a machine running Mac OSX, Windows, Linux or Solaris.

#### Vagrant
You will also need to have Vagrant installed, so that the VirtualBox VM can be
configured for the particular tools needed by this project. It can be
downloaded [here](https://www.vagrantup.com/downloads) and installed onto
a machine running Mac OSX, Windows, or Linux.

### Running the project
If the dependencies have been installed, you are ready to run launch the vagrant
virtual machine. 

So first, open the command prompt and navigate inside the project directory to 
the `vagrant/tournament/` folder, then type:

```
vagrant up
```

This will start the virtual machine and may take a minute or so. As long as no 
errors occurred, you should now be able to log into the machine through ssh, so
next type:

```
vagrant ssh
```

This should return a prompt that shows you logged in under the generic username
"vagrant". Now you need to move yourself to the shared directory between the VM
and your host machine:

```
cd /vagrant/
```

From here you'll find the course folders for each mini-project where database-seeding
specific to that project can be found
