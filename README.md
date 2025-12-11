# Gradebook

A Simple Python tool designed to help instructors manage student grades, visualize class performance, and generate individual report cards. Built with **Streamlit**, **Pandas**, and **Matplotlib**.

## try it
[**Click here to try the app**](https://gradebook-project-ryba7k6byddgiqkfx8e8oz.streamlit.app/)

## What It Does
* **Data Merging:** Automatically links student rosters, grade sheets, and quiz files into a single master view.
* **Visualizations:** Displays grade distribution (bar charts) and score density (KDE curves) to analyze class performance.
* **Custom Weighting:** Allows users to adjust the weight of exams, quizzes, and homework dynamically using sliders.
* **Student Reports:** Generates downloadable text reports and individual performance charts for any selected student.

## run localy
1.  Clone :
    ```bash
    git clone https://github.com/Abdelhadi-Wael/gradebook-project.git
    cd gradebook-project
    ```
2.  Install requirements:
    ```bash
    pip install -r requirements.txt
    ```
3.  run:
    ```bash
    streamlit run app.py
    ```

## Project Structure
* `app.py`: The main application script.
* `sample-data/`: CSV files provided for testing the interface.
* `requirements.txt`: List of necessary Python libraries.
