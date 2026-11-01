Summary
This project addresses the challenge of identifying individuals from visual information efficiently. Manual review of surveillance footage can be time-consuming and susceptible to human error. To investigate an automated approach, the project developed a web-based system combining deep learning and computer vision to support the identification of individuals represented in a predefined dataset of fugitive profiles. The system processes both uploaded videos and live webcam feeds.

Methodology
A dataset containing images of known fugitives was collected, annotated, preprocessed, and augmented using Roboflow. A YOLOv8 object-detection model was trained and validated using the prepared dataset. The trained model was integrated into a web application developed with HTML, CSS, Bootstrap, and JavaScript for the frontend, Python Flask for backend operations, and MySQL for managing user information and fugitive records. The system also incorporated user authentication and administrative record-management functionality.

Results
The completed prototype integrated the trained YOLOv8 model into a functional web-based identification workflow supporting uploaded videos and live webcam input. The application underwent functional testing and assessments covering usability, compatibility, performance, and security. These activities demonstrated the feasibility of combining deep learning-based detection with web application technologies. However, the project report does not provide independently verified quantitative benchmarks for detection accuracy or inference speed.

Individual Contribution
This project was completed collaboratively by three students. My contributions included preparing and processing image data, implementing the YOLOv8-based detection model, integrating the trained model into the web application, and developing the system's user-facing functionality. I also participated in debugging, integration testing, and evaluating the application's performance and functionality.

Conclusion
The project demonstrates the feasibility of integrating deep learning-based object detection into a web-based identification prototype. Its limitations include dependence on dataset quality and representativeness, variations in environmental conditions, computational requirements, and potential identification bias. Future improvements should focus on more representative training data, rigorous quantitative evaluation, inference optimization, and stronger safeguards for privacy and fairness. The project strengthened my practical understanding of artificial intelligence and computer vision.

Keywords: Deep Learning; Computer Vision; YOLOv8; Object Detection; Real-Time Identification; Python;

Flask; MySQL
