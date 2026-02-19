import cv2
import os

name=input("Enter Name: ")
capture_limit=250
save_path=f"dataset/{name}"
os.makedirs(save_path,exist_ok=True)

faceCascade=cv2.CascadeClassifier(
    cv2.data.haarcascades+'haarcascade_frontalface_default.xml'
)

cap=cv2.VideoCapture(1)
count=0

while True:
    ret,frame=cap.read()
    gray=cv2.cvtColor(frame,cv2.COLOR_BGR2GRAY)

    faces=faceCascade.detectMultiScale(gray,1.3,5)

    for(x,y,w,h) in faces:
        face=gray[y:y+h,x:x+w]
        count+=1
        cv2.imwrite(f"{save_path}/{count}.jpg",face)

        cv2.rectangle(frame,(x,y),(x+w,y+h),(0,255,0),2)

    cv2.imshow("Register Face",frame)

    if count>=capture_limit:
        break

    if cv2.waitKey(1)==27:
        break

cap.release()
cv2.destroyAllWindows()
print("Face Scan Complete")
