import streamlit as st
import os
import json
import yaml
import openai
from time import sleep  # Import sleep from time module
from dotenv import load_dotenv

# Load .env file

load_dotenv()

def generate_summary(messages):
    return ' '.join(messages)

def generate_consensus_summary(messages, model):
    synthesized_policy = open_file('summary.txt')
    messages = [{'role': 'system', 'content': synthesized_policy}, {'role': 'user', 'content': 'What is the consensus based on the personalities involved?'}] + messages
    return chatbot(messages, model)

def save_yaml(filepath, data):
    with open(filepath, 'w', encoding='utf-8') as file:
        yaml.dump(data, file, allow_unicode=True)

def open_file(filepath):
    with open(filepath, 'r', encoding='utf-8', errors='ignore') as infile:
        return infile.read()

def get_persona_traits(filepath='persona_traits.json'):
    with open(filepath, 'r') as f:
        return json.load(f)['MBTI Personality Types']


def chatbot(messages, model, temperature=0.8):
    openai_api_key = os.getenv("OPENAI_API_KEY")
    openai.api_key = openai_api_key

    response = openai.ChatCompletion.create(model=model, messages=messages, temperature=temperature)
    return response['choices'][0]['message']['content']

def perform_step(selected_personalities, current_persona_idx, response_list, issue, model):
    next_persona = selected_personalities[current_persona_idx % len(selected_personalities)]
    traits = get_persona_traits()[next_persona]
    system_with_traits = open_file('system_persona_role.txt').replace('<<PERSONA>>', traits)
    last_four_messages = response_list[-4:]
    messages = [{'role': 'system', 'content': system_with_traits}, {'role': 'user', 'content': f"What are your thoughts on this proposed policy: {issue}?"}] + [{'role': 'assistant', 'content': msg.split(": ")[1]} for msg in last_four_messages]
    response = chatbot(messages, model)
    formatted_response = f"{next_persona}: {response}"
    response_list.append(formatted_response)
    st.session_state.response_list = response_list
    st.session_state.current_persona_idx = (current_persona_idx + 1) % len(selected_personalities)

def main():
    st.title("Automated Consensus")
    model = st.selectbox('Choose a model', ['gpt-3.5-turbo', 'gpt-4'], index=1)
    selected_personalities = st.multiselect("Which MBTI personalities do you want to include?", list(get_persona_traits().keys()))
    issue = st.text_input("")

    auto_approve = st.session_state.get('auto_approve', False)

    col1, col2, col2_5, col3, col4, col_space, col5 = st.columns([0.23, 0.23, 0.23, 0.22, 0.08, 0.05, 0.15])
    start_debate_button = col1.button("start debate")
    step_button = col2.button("perform step")
    five_steps_button = col2_5.button("5 steps")



    if col4.markdown(
        f"""
        <label class="switch">
        <input type="checkbox" {"checked" if auto_approve else ""} onclick="updateAutoApprove(this)">
        <span class="slider round"></span>
        </label>
        <script>
        function updateAutoApprove(element) {{
            let value = element.checked;
            Streamlit.setComponentValue('auto_approve', value);
        }}
        </script>

        <style>
        .switch {{
            position: relative;
            display: inline-block;
            width: 60px;
            height: 34px;
        }}
        .switch input {{display:none;}}
        .slider {{
            position: absolute;
            cursor: pointer;
            top: 0;
            left: 0;
            right: 0;
            bottom: 0;
            background-color: #ccc;
            -webkit-transition: .4s;
            transition: .4s;
        }}
        .slider:before {{
            position: absolute;
            content: "";
            height: 26px;
            width: 26px;
            left: 4px;
            bottom: 4px;
            background-color: white;
            -webkit-transition: .4s;
            transition: .4s;
        }}
        input:checked + .slider {{
            background-color: #2196F3;
        }}
        input:focus + .slider {{
            box-shadow: 0 0 1px #2196F3;
        }}
        input:checked + .slider:before {{
            -webkit-transform: translateX(26px);
            -ms-transform: translateX(26px);
            transform: translateX(26px);
        }}
        .slider.round {{
            border-radius: 34px;
        }}
        .slider.round:before {{
            border-radius: 50%;
        }}
        </style>
        """,
        unsafe_allow_html=True,
    ):
        pass
    archive_button = col5.button("archive")

    st.session_state.auto_approve = st.session_state.get('auto_approve', False)


    response_list = st.session_state.get("response_list", [])
    current_persona_idx = st.session_state.get("current_persona_idx", 0)

    if start_debate_button:
        response_list = []  # Reset the response list
        # Generate only the first response
        personality_type = selected_personalities[0]
        traits = get_persona_traits()[personality_type]
        system_with_traits = open_file('system_persona_role.txt').replace('<<PERSONA>>', traits)
        messages = [{'role': 'system', 'content': system_with_traits}, {'role': 'user', 'content': f"What do you think this persona will think about {issue}?"}]
        response = chatbot(messages, model)
        formatted_response = f"{personality_type}: {response}"
        response_list.append(formatted_response)
        st.session_state.response_list = response_list
        st.session_state.current_persona_idx = 1  # Next index to be processed

    if archive_button:
        # Read system message from 'summary.txt'
        system_message = open_file('summary.txt')
        # Generate summary
        summary = generate_summary([system_message] + response_list)
        # Print the summary
        st.write(f"### Generated Summary:")
        st.write(summary)


    if step_button or (auto_approve and len(response_list) >= len(selected_personalities)):
        next_persona = selected_personalities[current_persona_idx % len(selected_personalities)]
        traits = get_persona_traits()[next_persona]
        system_with_traits = open_file('system_persona_role.txt').replace('<<PERSONA>>', traits)
        last_four_messages = response_list[-4:]
        messages = [{'role': 'system', 'content': system_with_traits}, {'role': 'user', 'content': f"What are your thoughts on this proposed policy: {issue}?"}] + [{'role': 'assistant', 'content': msg.split(": ")[1]} for msg in last_four_messages]
        response = chatbot(messages, model)
        formatted_response = f"{next_persona}: {response}"
        response_list.append(formatted_response)
        st.session_state.response_list = response_list
        st.session_state.current_persona_idx = (current_persona_idx + 1) % len(selected_personalities)

    if step_button or (auto_approve and len(response_list) >= len(selected_personalities)):
        perform_step(selected_personalities, current_persona_idx, response_list, issue, model)

    if five_steps_button:
        for _ in range(5):
            perform_step(selected_personalities, current_persona_idx, response_list, issue, model)


    if five_steps_button:
        for _ in range(5):
            perform_step()
    if auto_approve and len(response_list) >= len(selected_personalities):
        sleep(1) 
        st.experimental_rerun()


    for response in response_list:
        st.markdown(f"`{response}`")

if __name__ == "__main__":
    main()
