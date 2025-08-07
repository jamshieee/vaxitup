## 🚫 License Notice

This project is protected under **All Rights Reserved**.

You may not:
- Copy
- Modify
- Distribute
- Publish
- Use this code in any form without explicit permission.

⚠ Unauthorized use may result in legal action.


\# Vaccine Center Registration System 


A web-based registration system built using \*\*Django\*\* for registering vaccine centers across Kerala.



\## 📌 Features



\- Register vaccine centers with ID, contact info, location, and login credentials

\- Responsive front-end with HTML/CSS

\- Data stored in PostgreSQL / SQLite (customizable)

\- User authentication (center login)



\##Tech Stack



\- \*\*Backend:\*\* Django (Python)

\- \*\*Frontend:\*\* HTML5, CSS3, Bootstrap, Js

\- \*\*Database:\*\* SQLite (default), can be upgraded to PostgreSQL

\- \*\*Version Control:\*\* Git \& GitHub



\##Setup Instructions



1\. \*\*Clone the repo:\*\*



```bash

git clone https://github.com/your-username/your-repo.git

cd your-repo

2. python -m venv env  \env\Scripts\activate  # for Windows

3. Create a Database using Postgres or MySQL and change the settings.py

5. pip install -r requirements.txt

4. In settings.py add Email and app password
	Go to your Google Account settings at myaccount.google.com.

&nbsp;	Click on "Security" in the left menu.

&nbsp;	Under "Signing in to Google," select "2-Step Verification".

&nbsp;	Scroll down to the "App passwords" section and click on it.

&nbsp;	You may need to sign in again.

&nbsp;	Select the app and device you want to generate a password for (e.g., "Mail" and "Other 		(Custom name)").

&nbsp;	Enter a name to identify the app or device (e.g., "My Software").

&nbsp;	Click "Create".

&nbsp;	A 16-digit app password will be generated. Copy and save it securely, as it cannot be 	viewed again.


5. Now run makemigrations and migrate

6. Now you can access the project by running python manage.py runserver



