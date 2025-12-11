import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

st.set_page_config(page_title="Gradebook", layout="wide")
plt.style.use('ggplot')

class Gradebook:
    def __init__(self, roster_file, grades_file, quiz_files):
        # Initialize the Gradebook with raw files #
        self.roster_file = roster_file
        self.grades_file = grades_file
        self.quiz_files = quiz_files
        self.df = None

    def load_data(self):
        # Reads CSV files and merges them into self.df #

        # roster
        roster = pd.read_csv(
            self.roster_file,
            index_col = "NetID",
            usecols = ["Section", "Email Address", "NetID"],
            converters = {"NetID": str.lower, "Email Address": str.lower}
        )

        # grades
        grades = pd.read_csv(
            self.grades_file,
            index_col = "SID", # same as NetID
            usecols = lambda x: "Submission" not in x,
            converters = {"SID": str.lower}
        )

        # quizzes
        quiz_df = pd.DataFrame()
        for f in self.quiz_files:
            q_name = " ".join(f.name.lower().replace(".csv", "").title().split("_")[:2])
            q_data = pd.read_csv(
                f, index_col = "Email", usecols=["Email", "Grade"],
                converters = {"Email": str.lower}
             ).rename(columns={"Grade": q_name})
            quiz_df = pd.concat([quiz_df, q_data], axis=1)

        # merge
        self.df = pd.merge(roster, grades, left_index=True, right_index=True)
        if not quiz_df.empty:
            self.df = pd.merge(self.df, quiz_df, left_on="Email Address", right_index=True, how="left")

        self.df.fillna(0)

    def calculate_grades(self, weights):
        # Calculates final scores #
        if self.df is None: return

        df = self.df
        # exams
        for n in range(1, 4):
            if f"Exam {n}" in df:
                df[f"Exam {n} Score"] = df[f"Exam {n}"] / df[f"Exam {n} - Max Points"]

        # homework
        hw_cols = df.filter(regex=r"^Homework \d\d?$")
        hw_max = df.filter(regex=r"^Homework \d\d? - Max Points$")
        df["Homework Score"] = hw_cols.sum(axis=1) / hw_max.sum(axis=1)

        # quizzes
        q_cols = df.filter(regex=r"^Quiz")
        if not q_cols.empty:
            # quiz file does not give the max score so we assume that max grade is the max grade
            q_scores = q_cols / q_cols.max()
            df["Quiz Score"] = q_scores.mean(axis=1)
        else:
            df["Quiz Score"] = 0.0


        # validate weights
        w_series = pd.Series(weights)
        valid_weights = []
        for w in w_series.index:
            if w in df.columns:
                valid_weights.append(w)

        df["Final Score"] = (df[valid_weights].fillna(0) * w_series[valid_weights]).sum(axis=1)
        df["Ceiling Score"] = np.ceil(df["Final Score"] * 100)

        grades = {90: "A", 80: "B", 70: "C", 60: "D", 0: "F"}
        def get_letter(val):
            for k, v in grades.items():
                if val >= k: return v
            return None

        df["Final Grade"] = df["Ceiling Score"].apply(get_letter)

    def render_dashboard(self):
        # Draws the streamlit UI #
        if self.df is None: return

        st.title("Gradebook")
        tab1, tab2, tab3, tab4 = st.tabs(["Summary", "Visuals", "Export", "Student Report"])

        with tab1:
            desired_cols = ["First Name", "Last Name", "Email Address", "Ceiling Score", "Final Grade"]
            table = self.df[desired_cols]
            st.dataframe(
                table,
                height=800,
                column_config={"_index": "ID"}
            )

        with tab2:
            c1, c2 = st.columns(2)
            chart_size = (6, 6)
            with c1:
                st.subheader("Grade Counts")

                # how many students got each grade (a , b , ...)
                grade_counts = self.df["Final Grade"].value_counts().sort_index()
                fig, ax = plt.subplots(figsize=chart_size)
                grade_counts.plot.bar(ax=ax, color="tab:blue")
                ax.set_ylabel("Number of Students")
                ax.set_xlabel("Letter Grade")

                plt.tight_layout() # removes extra spaces
                st.pyplot(fig)

            with c2:
                st.subheader("Score Distribution")
                fig, ax = plt.subplots(figsize=chart_size)

                # histogram
                self.df["Final Score"].plot.hist(bins=20, density=True, ax=ax, alpha=0.5, color="blue")
                # density curve
                self.df["Final Score"].plot.density(ax=ax, color='red', linewidth=2)

                ax.set_xlabel("Final Score")
                ax.set_ylabel("Density")
                plt.tight_layout()
                st.pyplot(fig)

        with tab3:
            st.download_button("Download Full Gradebook", self.df.to_csv().encode("utf-8"), "grades.csv")

            for section_name, section_data in self.df.groupby("Section"):
                st.download_button(
                label=f"Download Section {section_name}", data=section_data.to_csv().encode("utf-8"), file_name=f"Section_{section_name}.csv")

        with tab4:
            if "Last Name" in self.df:
                # create lookup dictionary for easier search
                # Key = "Doe, John (jdoe25)"  -> Value = "jdoe25"
                student_map = {
                    f"{row['Last Name']}, {row['First Name']} ({netid})": netid
                    for netid, row in self.df.iterrows()
                }
                selected_name = st.selectbox("Search for a Student", options=student_map.keys())
                if selected_name:
                    student_id = student_map[selected_name]
                    self.generate_student_report(student_id)

    def generate_student_report(self, student_id):
        # Generates a detailed summary and chart for a single student #
        student = self.df.loc[student_id]

        # get scores
        ex1 = student.get("Exam 1 Score", 0) * 100
        ex2 = student.get("Exam 2 Score", 0) * 100
        ex3 = student.get("Exam 3 Score", 0) * 100
        hw = student.get("Homework Score", 0) * 100
        qz = student.get("Quiz Score", 0) * 100
        class_avg = self.df['Final Score'].mean() * 100

        # txt report
        report = f"""
        STUDENT: {student['First Name']} {student['Last Name']} ({student.name})
        GRADE:   {student['Final Grade']} ({student['Ceiling Score']:.0f}%)
        AVG:     {class_avg:.1f}%
        -----------------------------------
        Exam 1: {ex1:.1f}%
        Exam 2: {ex2:.1f}%
        Exam 3: {ex3:.1f}%
        HW:     {hw:.1f}%
        Quiz:   {qz:.1f}%
        """
        st.text(report)

        # draw chart
        fig, ax = plt.subplots(figsize=(6, 2))

        # Lists for plotting
        labels = ["Ex1", "Ex2", "Ex3", "HW", "QZ"]
        scores = [ex1, ex2, ex3, hw, qz]
        bars = ax.bar(labels, scores)
        ax.set_ylim(0, 115)
        ax.set_title(f"Grades: {student['First Name']}")

        ax.bar_label(bars, fmt='%.0f%%', padding=3, color='black')
        st.pyplot(fig)

        st.download_button("Download Report", report, f"{student['Last Name']}_Report.txt")


# file uploads
st.sidebar.header("Data Files")
r_file = st.sidebar.file_uploader("Roster", type="csv")
g_file = st.sidebar.file_uploader("Grades", type="csv")
q_files = st.sidebar.file_uploader("Quizzes", type="csv", accept_multiple_files=True)

st.sidebar.divider()
st.sidebar.header("Weights")
weights_input = {
    "Exam 1 Score": st.sidebar.slider("Exam 1", 0.0, 1.0, 0.05),
    "Exam 2 Score": st.sidebar.slider("Exam 2", 0.0, 1.0, 0.10),
    "Exam 3 Score": st.sidebar.slider("Exam 3", 0.0, 1.0, 0.15),
    "Quiz Score": st.sidebar.slider("Quiz", 0.0, 1.0, 0.30),
    "Homework Score": st.sidebar.slider("Homework", 0.0, 1.0, 0.40)
}

if r_file and g_file:
    if sum(weights_input.values()) != 1.0:
        st.error(f"Weights sum to {sum(weights_input.values()):.2f}. Must be 1.0.")
    else:
        gradebook = Gradebook(r_file, g_file, q_files)
        gradebook.load_data()
        gradebook.calculate_grades(weights_input)
        gradebook.render_dashboard()
else:
    st.info("Upload Roster and Grades to begin.")

