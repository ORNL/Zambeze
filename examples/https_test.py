import requests


url = "http://127.0.0.1:5000/download"

response = requests.get(url, json={'file_name': '/Users/6o1/Desktop/testfile.txt'})
file_name = 'testfile.txt'

if response.status_code == 200:
    # Save the received file with the same name
    with open(file_name, 'wb') as f:
        f.write(response.content)
    print(f"File '{file_name}' downloaded successfully.")
else:
    print("File not found on the server.")


