[Previous content up to line 403]
def main():
    # Set page configuration
    st.set_page_config(
        page_title="Video Subtitling and Translation Tool",
        page_icon="🎬",
        layout="wide",
        menu_items={
            'Get Help': 'https://subtool-trkn.replit.app',
            'Report a bug': 'https://subtool-trkn.replit.app',
            'About': '© 2024 trhacknon - A powerful video subtitling and translation tool'
        }
    )

    # Add SEO and social meta tags
    st.components.v1.html('''
        <meta name="description" content="Process videos, generate transcriptions, and create translations using OpenAI's Whisper and GPT-4 APIs">
        <meta name="author" content="trhacknon">
        <meta property="og:type" content="website">
        <meta property="og:url" content="https://subtool-trkn.replit.app">
        <meta property="og:title" content="Video Subtitling and Translation Tool">
        <meta property="og:description" content="Automatic video subtitling and translation with OpenAI">
        <meta property="og:image" content="https://subtool-trkn.replit.app/icon.png">
        <meta property="twitter:card" content="summary_large_image">
        <meta property="twitter:url" content="https://subtool-trkn.replit.app">
        <meta property="twitter:title" content="Video Subtitling and Translation Tool">
        <meta property="twitter:description" content="Automatic video subtitling and translation with OpenAI">
        <meta property="twitter:image" content="https://subtool-trkn.replit.app/icon.png">
    ''', height=0)

    st.title("Video Subtitling and Translation Tool")

[Rest of the existing main function content]
