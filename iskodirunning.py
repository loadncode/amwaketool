import socket
import json

def runcheck():
    rpc = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try: rpc.connect(('localhost', 9090))
    except socket.error:
        return False
    else:
        rpc.sendall('{"jsonrpc":"2.0","method":"JSONRPC.Ping","id":1}')
        while True:
            data,addr = rpc.recvfrom(1024)
            if data:
                break
        rpc.close()
        thing = json.loads(data)
        if thing['result'] == 'pong':
            return True
        else:
            return False # should report an error here, since this should not happen
    finally: rpc.close()
