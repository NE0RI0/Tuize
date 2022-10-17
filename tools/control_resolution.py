import cv2
from time import sleep

cap = cv2.VideoCapture(0, cv2.CAP_DSHOW) # this is the magic!

cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)

sleep(2)
r, frame = cap.read()
...
print('Resolution: ' + str(frame.shape[0]) + ' x ' + str(frame.shape[1]))

while True:
    cv2.imshow("frame1", frame)
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break