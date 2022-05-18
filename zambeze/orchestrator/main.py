#main.py
# This is a main file which will initialise and execute the run method of our application

# Importing our application file
from services import Services

if __name__ == "__main__":
    # Initialising our application
    services = Services() 
    # Running our application 
    services.run()
