import pygame
import sys

GREEN = (34,187,51)

# Initialize Pygame
pygame.init()

# filepath: d:\learn\HK242\MMT_Lab\Assignment\testUI\main.py
font = pygame.font.SysFont("Arial", 36)
small_font = pygame.font.SysFont("Arial", 24)
emoji_font = pygame.font.Font("C:\\Windows\\Fonts\\seguiemj.ttf", 24)

# Set up the display
WIDTH = 660
HEIGHT = 400
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("My Torrent App")

# Colors
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
GRAY = (200, 200, 200)
GREEN = (0, 128, 0)
YELLOW = (255, 255, 0)

# Fonts
font = pygame.font.Font(None, 36)
small_font = pygame.font.Font(None, 24)

# Text input box
input_box = pygame.Rect(40, 50, 480, 40)
input_text = ""
active = False

# Browse button
browse_button = pygame.Rect(input_box.right - 70, input_box.y, 80, input_box.height)

# Start button
start_button = pygame.Rect(540, 50, 110, 40)

# File data (simulated)
files = [
    # {"name": "File name 1", "progress": 40, "paused": False},
    # {"name": "File name 2", "progress": 90, "paused": False},
    # {"name": "File name 3", "progress": 30, "paused": True},
    # {"name": "File name 4", "progress": 60, "paused": False},
]

# Pause/Resume buttons for each file
pause_buttons = [pygame.Rect(650-100, 115 + i * 50, 80, 30) for i in range(100)]


# Function to simulate starting a download
def start_download(link):
    print(f"Starting download with link: {link}")
    # In a real app, this would handle the torrent link and start the download
    # For now, we just print the link and simulate progress

# Main loop
clock = pygame.time.Clock()
running = True
def main():
    global running, active, input_text, files, pause_buttons
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

            # Handle input box
            if event.type == pygame.MOUSEBUTTONDOWN:
                if input_box.collidepoint(event.pos):
                    active = not active
                else:
                    active = False

                # Browse button click - open file explorer and update input_text
                if browse_button.collidepoint(event.pos):
                    import tkinter as tk
                    from tkinter import filedialog
                    root = tk.Tk()
                    root.withdraw()  # hide the tkinter window
                    file_path = filedialog.askopenfilename()
                    if file_path:
                        input_text = file_path
                        

                # Start button click
                if start_button.collidepoint(event.pos) and input_text:
                    start_download(input_text)
                    files.append({"name": input_text, "progress": 0, "paused": False})

                # Pause/Resume button clicks
                for i, button in enumerate(pause_buttons):
                    if button.collidepoint(event.pos):
                        files[i]["paused"] = not files[i]["paused"]

            # Handle text input
            if event.type == pygame.KEYDOWN:
                if active:
                    if event.key == pygame.K_RETURN:
                        active = False
                    elif event.key == pygame.K_BACKSPACE:
                        input_text = input_text[:-1]
                    else:
                        input_text += event.unicode

        # Clear the screen
        screen.fill(WHITE)

        # Draw the title
        title = font.render("My Torrent App", True, BLACK)
        screen.blit(title, (50, 10))

        # Draw the input box
        pygame.draw.rect(screen, BLACK, input_box, 2, border_radius=20)
        if not input_text:
            placeholder = small_font.render("Enter torrent file path here", True, GRAY)
            screen.blit(placeholder, (input_box.x + 10, input_box.y + 13)) # input text position
        else:
            max_width = input_box.width - 70  # 5 pixels padding on each side
            text_to_display = input_text
            
            # Truncate displayed text from the left if it's too wide
            while small_font.size(text_to_display)[0] > max_width and text_to_display:
                text_to_display = text_to_display[:-1]
            if text_to_display != input_text:
                text_to_display = text_to_display + "..."
            input_surface = small_font.render(text_to_display, True, BLACK)
            screen.blit(input_surface, (input_box.x + 5, input_box.y + 13))

        # Draw the Browse button next to the input box
        
        # pygame.draw.rect(screen, (100, 100, 100), browse_button, border_radius=8)
        # pygame.draw.rect(screen, BLACK, browse_button, 2, border_radius=10)
        browse_text = emoji_font.render("📁", True, BLACK)
        browse_text_rect = browse_text.get_rect(center=browse_button.center)
        screen.blit(browse_text, browse_text_rect)

        # Draw the start button with border
        pygame.draw.rect(screen, (34,187,51), start_button, border_radius=8)
        pygame.draw.rect(screen, BLACK, start_button, 2, border_radius=10)  # Border with thickness 2
        start_text_surface = emoji_font.render("✅START", True, BLACK)
        start_text_rect = start_text_surface.get_rect(center=start_button.center)
        screen.blit(start_text_surface, start_text_rect)

        # Draw the file list
        for i, file in enumerate(files):
            y_pos = 120 + i * 50

            # File outline rectangle (adjust position and size as needed)
            file_outline = pygame.Rect(40, y_pos - 10, 650 - 40, 40)
            pygame.draw.rect(screen, BLACK, file_outline, 2)

            # File name
            file_name = small_font.render(file["name"], True, BLACK)
            screen.blit(file_name, (50, y_pos))

            # Progress
            if file["paused"]:
                progress_text = f"Paused: {file['progress']}%"
            else:
                progress_text = f"Downloading: {file['progress']}%"
                if file["progress"] < 100:
                    file["progress"] += 1
                    print(file["progress"])

            progress = small_font.render(progress_text, True, BLACK)
            screen.blit(progress, (350, y_pos))

            # Pause/Resume button
            button = pause_buttons[i]
            pygame.draw.rect(screen, (240,173,78), button, border_radius=8)
            pygame.draw.rect(screen, BLACK, button, 2, border_radius=10)
            button_text = "PAUSE" if not file["paused"] else "RESUME"
            button_label = small_font.render(button_text, True, BLACK)
            label_rect = button_label.get_rect(center=button.center)
            screen.blit(button_label, label_rect)

        # Update the display
        pygame.display.flip()
        clock.tick(60)

if __name__ == "__main__":
    # Run the main loop
    main()

    # Quit Pygame
    pygame.quit()
    sys.exit()