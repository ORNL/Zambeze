import paramiko

username = "tskluzac"

transport = paramiko.Transport("frontier.olcf.ornl.gov")

transport.connect(username=username)

transport.auth_interactive_dumb(username, handler=None, submethods='')

sftp = paramiko.SFTPClient.from_transport(transport)

filepath = "/autofs/nccs-svm1_home2/tskluzac/hi-renan.txt"

localpath = "/tmp/hi-renan.txt"

sftp.get(filepath, localpath)

# Close

if sftp:
    sftp.close()

if transport:
    transport.close()