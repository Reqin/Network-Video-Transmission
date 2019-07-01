import cv2

cap = cv2.VideoCapture(0)
_, frame = cap.read()
print(_)
print(frame)
exit()
cv2.imshow('s', frame)
cv2.waitKey(1000)
