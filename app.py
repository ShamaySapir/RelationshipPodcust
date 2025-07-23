# imports
import gradio as gr
import src.functions as fn

def process_file(file, podcast_episode):
    if file is None:
        return "No file uploaded.", None, None

    # Step 1: Read text from the uploaded file
    with open(file.name, "r", encoding="utf-8") as f:
        text = f.read()

    # Step 2: Translate the Hebrew text to English
    translated = fn.translate_week_episodes(text)

    # Step 3: Split the translated text into days
    days = fn.divide_episodes(translated)

    # Step 4: Summarize each day's content
    summaries = fn.summarize_week_episodes(days, int(podcast_episode))

    # Step 5: Prepare the output text and input for audio generation
    output_text = ""
    for item in summaries:
        title = item["day"]
        summary = item["response"]
        output_text += f"{title}\n{summary}\n\n"

    # Step 6: Use the original translated day texts for audio
    audio_files = fn.generate_audio_files(days)


    # Step 7: Return all outputs to the UI
    return translated, output_text, audio_files


with gr.Blocks() as demo:
    gr.Markdown("## 🎧 RelationshipPodcust – הפוך טקסט לפודקאסט")
    
    with gr.Row():
        file_input = gr.File(label="העלה קובץ טקסט")
        episode_number = gr.Number(value=1, label="מספר פרק פודקאסט התחלתי")
    
    with gr.Row():
        translate_output = gr.Textbox(label="תרגום", lines=10)
        summary_output = gr.Textbox(label="סיכום", lines=10)

    run_button = gr.Button("צור סיכום")

    run_button.click(
        fn=process_file,
        inputs=[file_input, episode_number],
        outputs=[translate_output, summary_output]
    )

if __name__ == "__main__":
    demo.launch(share=True)

