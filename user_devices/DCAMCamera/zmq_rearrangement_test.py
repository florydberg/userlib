
import zmq
import time

context = zmq.Context()
publisher = context.socket(zmq.PUB)

# Same port used by your C++ receiver
publisher.bind("tcp://127.0.0.1:5556")

# Allow the subscriber to connect
time.sleep(2)

# Simulated 6x6 occupancy: 20 atoms
occupancy = (
    "101010"
    "010101"
    "110011"
    "101101"
    "000100"
    "100001"
)

assert len(occupancy) == 36

print("Fake occupancy:")
for row in range(6):
    print(occupancy[row*6:(row+1)*6])

try:
    while True:
        publisher.send_string(occupancy)
        print("Sent:", occupancy)
        time.sleep(2)
except KeyboardInterrupt:
    pass
finally:
    publisher.close()
    context.term()
