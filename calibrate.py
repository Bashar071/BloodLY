"""
Interactive calibration tool. Point your camera at a real tray of tubes to
find good THRESHOLD_VALUE and cap-color HSV ranges before running app.py.

Controls:
  - Move the trackbar to adjust the binary threshold used for tube detection
  - Click on a cap in the video window to print its HSV value in the console
  - Press 'q' to quit
"""
import cv2
import config

def on_mouse(event, x, y, flags, param):
    if event == cv2.EVENT_LBUTTONDOWN:
        hsv_frame = param
        print("HSV at click:", hsv_frame[y, x])

def nothing(x):
    pass

def main():
    cap = cv2.VideoCapture(config.CAMERA_INDEX)
    cv2.namedWindow("Threshold")
    cv2.createTrackbar("Thresh", "Threshold", config.THRESHOLD_VALUE, 255, nothing)
    cv2.namedWindow("Camera (click to sample HSV)")

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        blurred = cv2.GaussianBlur(gray, (5, 5), 0)
        t = cv2.getTrackbarPos("Thresh", "Threshold")
        _, thresh = cv2.threshold(blurred, t, 255, cv2.THRESH_BINARY_INV)

        hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
        cv2.setMouseCallback("Camera (click to sample HSV)", on_mouse, hsv)

        cv2.imshow("Threshold", thresh)
        cv2.imshow("Camera (click to sample HSV)", frame)

        if cv2.waitKey(1) & 0xFF == ord('q'):
            print(f"Final threshold: {t} -- put this in config.py as THRESHOLD_VALUE")
            break

    cap.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    main()  