from datetime import date, datetime, time

import pandas as pd
import requests
import streamlit as st


def load_csv(file):
    try:
        df = pd.read_csv(file)

        columns = df.columns
        if (
            "task_url" not in columns
            or "start_date" not in columns
            or "end_date" not in columns
        ):
            st.error(
                "The CSV file must have the following columns: task_url, start_date, end_date"  # noqa
            )
            return None

        return df
    except Exception as e:
        st.error(f"Error loading file: {e}")
        return None


def register_tasks(clickup_api_key, df):
    for _, row in df.iterrows():
        task_url = row["task_url"].strip()
        start_date = datetime.strptime(
            row["start_date"].strip(), "%Y-%m-%d %H:%M"
        )  # noqa
        end_date = datetime.strptime(row["end_date"].strip(), "%Y-%m-%d %H:%M")

        response = register_task(
            clickup_api_key,
            task_url,
            start_date,
            end_date,
        )

        st.session_state.responses.append(response)


def calculate_task_duration(start, end):
    return int((end - start).total_seconds() * 1000)


def register_task(clickup_api_key, task_url, start, end):
    if not clickup_api_key:
        st.info("Please add your ClickUp API key to continue.")
        st.stop()

    start_time_in_milliseconds = start.timestamp() * 1000

    duration = calculate_task_duration(
        start,
        end,
    )

    task_url_split = task_url.split("/")

    task_id = task_url_split[-1]
    team_id = task_url_split[-2] if task_url_split[-2] != "t" else None

    headers = {
        "Authorization": clickup_api_key,
        "Content-Type": "application/json",
    }
    url = f"https://api.clickup.com/api/v2/team/{team_id}/time_entries"
    query = {
        "custom_task_ids": "true",
        "team_id": team_id,
    }

    data = {
        "tid": task_id,
        "duration": duration,
        "start": start_time_in_milliseconds,
    }

    response = requests.post(url, headers=headers, json=data, params=query)
    status_code = response.status_code
    message = (
        response.json().get("err")
        if status_code != 200
        else f"Task {task_id} registered successfully."
    )

    return {
        "status_code": status_code,
        "message": message,
    }


def main():
    st.session_state.responses = []

    with st.sidebar:
        clickup_api_key = st.text_input(
            "ClickUp API Key",
            key="clickup_api_key",
            type="password",
            placeholder="Insert your ClickUp API key here...",
        )
        "[Get an ClickUp API key](https://app.clickup.com/settings/apps)"

    tab1, tab2 = st.tabs(["Only one task", "Multiple tasks"])

    with tab1:
        st.header("Register only one task")

        st.divider()

        task_url = st.text_input(
            "Task URL",
            placeholder="https://app.clickup.com/t/459155/AQPOPS-372",
        )

        col1, col2 = st.columns(2)

        with col1:
            st.session_state.start_date = st.date_input(
                "Start date",
                date.today(),
            )

        with col2:
            st.session_state.start_time = st.time_input(
                "Set the task start time",
                time(8, 00),
            )

        col1, col2 = st.columns(2)

        with col1:
            st.session_state.end_date = st.date_input(
                "End date",
                date.today(),
            )

        with col2:
            st.session_state.end_time = st.time_input(
                "Set the task end time",
                time(9, 00),
            )

        st.divider()

        register_only_task = st.button(
            "Register",
            type="primary",
            key="confirm",
        )

        if register_only_task:
            if not task_url:
                st.info("Please add your task URL.")
                st.stop()

            st.session_state.responses = []

            start_date = st.session_state.start_date
            start_time = st.session_state.start_time
            end_date = st.session_state.end_date
            end_time = st.session_state.end_time

            start = datetime.datetime.combine(start_date, start_time)
            end = datetime.datetime.combine(end_date, end_time)

            response = register_task(
                clickup_api_key,
                task_url,
                start,
                end,
            )

            st.session_state.responses.append(response)

        for response in st.session_state.responses:
            status_code = response.get("status_code")
            message = response.get("message")

            st.info(f"[STATUS CODE: {status_code}] {message}")

    with tab2:
        st.header("Register multiple tasks")

        st.divider()

        uploaded_file = st.file_uploader(
            "Choose a CSV file", accept_multiple_files=False, type="csv"
        )

        with open("data.csv", "r") as file:
            st.download_button(
                label="Download template",
                data=file,
                file_name="data.csv",
                mime="text/csv",
            )

        if uploaded_file is not None:
            df = load_csv(uploaded_file)

            if df is not None:
                register_multiple_tasks = st.button(
                    "Register",
                    type="primary",
                    key="confirm_multiple_tasks",
                )

                if register_multiple_tasks:
                    register_tasks(clickup_api_key, df)

                    for response in st.session_state.responses:
                        status_code = response.get("status_code")
                        message = response.get("message")

                        st.info(f"[STATUS CODE: {status_code}] {message}")


main()
