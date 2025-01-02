# WebSearch_tab.py
# Gradio UI for performing web searches with aggregated results
#
# Imports
import asyncio

#
# External Imports
import gradio as gr

from App_Function_Libraries.Web_Scraping.WebSearch_APIs import generate_and_search, analyze_and_aggregate


#
# Local Imports

#
########################################################################################################################
#
# Functions:

def create_websearch_tab():
    with gr.TabItem("Web Search & Review", visible=True):
        with gr.Blocks() as perplexity_interface:
            gr.Markdown("# Perplexity-Style Search Interface")

            # State variables for managing the review process
            state = gr.State({
                "phase1_results": None,
                "search_params": None,
                "selected_results": []
            })

            with gr.Row():
                with gr.Column():
                    # Input components
                    question_input = gr.Textbox(
                        label="Enter your question",
                        placeholder="What would you like to know?",
                        lines=2
                    )

                    with gr.Row():
                        search_engine = gr.Dropdown(
                            choices=["google", "bing", "duckduckgo", "brave"],
                            value="google",
                            label="Search Engine"
                        )
                        result_count = gr.Slider(
                            minimum=1,
                            maximum=20,
                            value=10,
                            step=1,
                            label="Number of Results"
                        )

                    with gr.Row():
                        content_country = gr.Dropdown(
                            choices=["US", "UK", "CA", "AU"],
                            value="US",
                            label="Content Country"
                        )
                        search_lang = gr.Dropdown(
                            choices=["en", "es", "fr", "de"],
                            value="en",
                            label="Search Language"
                        )

                # Status displays
                with gr.Row():
                    search_btn = gr.Button("Search", variant="primary")
                    status_display = gr.Markdown(
                        value="Ready",
                        label="Status",
                        elem_classes="status-display"
                    )
                    progress_display = gr.HTML(
                        value='<div class="progress-bar" style="display: none;"></div>',
                        visible=True
                    )



        with gr.Row():
            # Results review section
            with gr.Column(visible=False) as review_column:
                gr.Markdown("### Review Search Results")
                results_review = gr.Dataframe(
                    headers=["Select", "Title", "URL", "Content Preview"],
                    datatype=["bool", "str", "str", "str"],
                    label="Search Results",
                    interactive=True
                )
                confirm_selection_btn = gr.Button("Generate Answer from Selected Results")

        with gr.Row():
            # Final output section
            with gr.Column(visible=False) as output_column:
                answer_output = gr.Markdown(label="Answer")
                sources_output = gr.JSON(label="Sources")

        # Add CSS for status styling
        gr.HTML("""
            <style>
                .status-display {
                    padding: 10px;
                    border-radius: 5px;
                    margin: 10px 0;
                }
                .status-normal { background-color: #f0f0f0; }
                .status-processing { background-color: #fff3cd; }
                .status-error { background-color: #f8d7da; }
                .status-success { background-color: #d4edda; }
                
                .progress-bar {
                    width: 100%;
                    height: 4px;
                    background: linear-gradient(to right, #4CAF50 0%, #4CAF50 50%, #f0f0f0 50%, #f0f0f0 100%);
                    background-size: 200% 100%;
                    animation: progress 1s linear infinite;
                }
                
                @keyframes progress {
                    0% { background-position: 100% 0; }
                    100% { background-position: -100% 0; }
                }
            </style>
        """)

        # Event handlers
        def update_status(message, status_type="normal"):
            status_classes = {
                "normal": "status-normal",
                "processing": "status-processing",
                "error": "status-error",
                "success": "status-success"
            }
            progress_visibility = status_type == "processing"
            return (
                gr.Markdown(value=message, elem_classes=status_classes[status_type]),
                gr.HTML(visible=progress_visibility)
            )

        def initial_search(question, engine, count, country, lang, state):
            try:
                # Update status to processing
                status, progress = update_status("Initializing search...", "processing")
                yield status, progress, state, [], gr.Column(visible=False), gr.Column(visible=False)

                search_params = {
                    "engine": engine,
                    "content_country": country,
                    "search_lang": lang,
                    "output_lang": lang,
                    "result_count": count,
                    "subquery_generation": True,
                    "subquery_generation_llm": "openai",
                    "relevance_analysis_llm": "openai",
                    "final_answer_llm": "openai"
                }

                status, progress = update_status("Generating sub-queries...", "processing")
                yield status, progress, state, [], gr.Column(visible=False), gr.Column(visible=False)

                phase1_results = generate_and_search(question, search_params)

                status, progress = update_status("Processing search results...", "processing")
                yield status, progress, state, [], gr.Column(visible=False), gr.Column(visible=False)

                review_data = []
                for idx, result in enumerate(phase1_results["web_search_results_dict"]["results"]):
                    review_data.append([
                        False,
                        result.get("title", "No title"),
                        result.get("url", "No URL"),
                        result.get("content", "No content")[:200] + "..."
                    ])

                state = {
                    "phase1_results": phase1_results,
                    "search_params": search_params,
                    "selected_results": []
                }

                status, progress = update_status("Search completed successfully!", "success")
                yield status, progress, state, review_data, gr.Column(visible=True), gr.Column(visible=False)

            except Exception as e:
                error_message = f"Error during search: {str(e)}"
                status, progress = update_status(error_message, "error")
                yield status, progress, state, [], gr.Column(visible=False), gr.Column(visible=False)

        def generate_final_answer(selected_results, state):
            try:
                status, progress = update_status("Generating final answer...", "processing")
                yield status, progress, "Processing...", {}, gr.Column(visible=False)

                if not state["phase1_results"] or not state["search_params"]:
                    raise ValueError("No search results available")

                filtered_results = {}
                all_results = state["phase1_results"]["web_search_results_dict"]["results"]
                for idx, (is_selected, _, _, _) in enumerate(selected_results):
                    if is_selected and idx < len(all_results):
                        filtered_results[str(idx)] = all_results[idx]

                if not filtered_results:
                    raise ValueError("No results selected")

                status, progress = update_status("Analyzing selected results...", "processing")
                yield status, progress, "Analyzing...", {}, gr.Column(visible=False)

                phase2_results = asyncio.run(analyze_and_aggregate(
                    {"results": filtered_results},
                    state["phase1_results"]["sub_query_dict"],
                    state["search_params"]
                ))

                status, progress = update_status("Answer generated successfully!", "success")
                yield status, progress, phase2_results["final_answer"]["Report"], phase2_results["final_answer"][
                    "evidence"], gr.Column(visible=True)

            except Exception as e:
                error_message = f"Error generating answer: {str(e)}"
                status, progress = update_status(error_message, "error")
                yield status, progress, "Error occurred while generating answer", {}, gr.Column(visible=False)

        # Connect event handlers
        search_btn.click(
            fn=initial_search,
            inputs=[
                question_input,
                search_engine,
                result_count,
                content_country,
                search_lang,
                state
            ],
            outputs=[
                status_display,
                progress_display,
                state,
                results_review,
                review_column,
                output_column
            ]
        )

        confirm_selection_btn.click(
            fn=generate_final_answer,
            inputs=[
                results_review,
                state
            ],
            outputs=[
                status_display,
                progress_display,
                answer_output,
                sources_output,
                output_column
            ]
        )

    return perplexity_interface

#
# End of File
########################################################################################################################
