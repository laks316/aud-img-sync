import streamlit as st
from moviepy.editor import *
import tempfile
from pathlib import Path
import os
import time
from PIL import Image
import io

def create_video(image_paths, audio_paths, duration_per_slide, progress_callback):
    """Create video from images and audio files."""
    try:
        # Create clips for each image
        image_clips = []
        for img_path in image_paths:
            clip = ImageClip(img_path).set_duration(duration_per_slide)
            image_clips.append(clip)
            progress_callback(20)  # Update progress after image processing
        
        # Load and set audio for each clip
        for i, (clip, audio_path) in enumerate(zip(image_clips, audio_paths)):
            audio = AudioFileClip(audio_path).set_duration(duration_per_slide)
            image_clips[i] = clip.set_audio(audio)
            progress_callback(40 + i * 10)  # Update progress after each audio processing
        
        # Concatenate all clips
        final_clip = concatenate_videoclips(image_clips, method="compose")
        progress_callback(80)  # Update progress after concatenation
        
        # Write output
        output_path = "output_video.mp4"
        final_clip.write_videofile(output_path, fps=24, codec='libx264', audio_codec='aac')
        progress_callback(100)  # Final progress update
        
        return output_path
        
    except Exception as e:
        raise Exception(f"Error creating video: {str(e)}")

def main():
    st.set_page_config(page_title="Photo & Audio Video Synchronizer", layout="wide")
    
    # Add custom CSS
    st.markdown("""
        <style>
        .main {
            padding: 2rem;
        }
        .stButton>button {
            width: 100%;
            margin-top: 1rem;
        }
        .uploaded-files {
            background-color: #f0f2f6;
            padding: 1rem;
            border-radius: 0.5rem;
            margin: 1rem 0;
        }
        </style>
    """, unsafe_allow_html=True)
    
    # Title and description
    st.title("📽️ Photo & Audio Video Synchronizer")
    st.markdown("""
    Create beautiful videos by combining your photos with audio files. 
    Each photo will be shown while its corresponding audio plays.
    """)

    #os.system('rm -rf temmp_fold')
    
    # Initialize session state for file storage
    if 'image_files' not in st.session_state:
        st.session_state.image_files = []
    if 'audio_files' not in st.session_state:
        st.session_state.audio_files = []
    
    # Create two columns for file uploads
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("📸 Upload Images")
        uploaded_images = st.file_uploader(
            "Choose image files (JPG, PNG)",
            type=["jpg", "jpeg", "png"],
            accept_multiple_files=True,
            key="image_upload"
        )
        
        if uploaded_images:
            st.session_state.image_files = uploaded_images
            st.markdown("### 🖼️ Uploaded Images")
            image_cols = st.columns(3)
            for idx, img_file in enumerate(uploaded_images):
                with image_cols[idx % 3]:
                    img = Image.open(img_file)
                    st.image(img, caption=f"Image {idx + 1}", use_column_width=True)
    
    with col2:
        st.subheader("🎵 Upload Audio")
        uploaded_audio = st.file_uploader(
            "Choose audio files (MP3, WAV)",
            type=["mp3", "wav"],
            accept_multiple_files=True,
            key="audio_upload"
        )
        
        if uploaded_audio:
            st.session_state.audio_files = uploaded_audio
            st.markdown("### 🎧 Uploaded Audio Files")
            for idx, audio_file in enumerate(uploaded_audio):
                st.audio(audio_file, format=f'audio/{audio_file.type.split("/")[1]}')
    
    # Settings
    st.markdown("---")
    st.subheader("⚙️ Settings")
    col3, col4 = st.columns(2)
    
    with col3:
        duration = st.slider(
            "Duration per slide (seconds)",
            min_value=1,
            max_value=20,
            value=5,
            help="How long each image should be shown"
        )
    
    with col4:
        video_quality = st.select_slider(
            "Video Quality",
            options=["Low", "Medium", "High"],
            value="Medium",
            help="Higher quality will take longer to process"
        )
    
    # Create video button
    if st.button("🎬 Create Video"):
        if not uploaded_images or not uploaded_audio:
            st.error("Please upload both images and audio files!")
            return
            
        if len(uploaded_images) != len(uploaded_audio):
            st.error("Number of images must match number of audio files!")
            return
        
        # Create progress bar and status
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        try:
            #st.write(os.getcwd())
            #os.system('rm -rf temmp_fold')
            os.mkdir('temmp_fold')
            #with tempfile.TemporaryDirectory() as temp_dir:
            temp_dir = 'temmp_fold'
            #with temp_dir1 as temp_dir:  
            #st.write(os.getcwd())  
            # Save uploaded files to temporary directory
            image_paths = []
            audio_paths = []
                
            status_text.text("Saving uploaded files...")
            for idx, (img, audio) in enumerate(zip(uploaded_images, uploaded_audio)):
                    # Save image
                    img_path = os.path.join(temp_dir, f"image_{idx}.jpg")
                    Image.open(img).save(img_path)
                    image_paths.append(img_path)
                    
                    # Save audio
                    audio_path = os.path.join(temp_dir, f"audio_{idx}.{audio.type.split('/')[1]}")
                    with open(audio_path, "wb") as f:
                        f.write(audio.getvalue())
                    audio_paths.append(audio_path)
                
            status_text.text("Creating video... This may take a few minutes.")
                
            # Create video with progress updates
            def update_progress(value):
                    progress_bar.progress(int(value))

            #st.write(image_paths)
            #st.write(audio_paths)
            #st.write(duration)
                    
            output_path = create_video(image_paths, audio_paths, duration, update_progress)
                
            # Offer video download
            with open(output_path, "rb") as f:
                video_bytes = f.read()
                    
            status_text.success("Video created successfully!")
            st.download_button(
                    label="⬇️ Download Video",
                    data=video_bytes,
                    file_name="photo_audio_video.mp4",
                    mime="video/mp4"
                )
                
            # Display the video
            #st.video(video_bytes)

            col1,col2=st.columns([1,3])

            with col1:
                st.video(video_bytes)

            #os.remove(temp_dir)
                
        except Exception as e:
            status_text.error(f"Error: {str(e)}")
            st.error("Please try again with different files or settings.")
            
        finally:
            # Clean up any temporary files
            if 'output_path' in locals():
                try:
                    os.remove(output_path)
                except:
                    pass

if __name__ == "__main__":
    main()
