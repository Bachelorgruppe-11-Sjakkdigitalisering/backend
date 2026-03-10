import customtkinter
import subprocess

class App(customtkinter.CTk):
  def __init__(self):
    super().__init__()
    self.geometry("400x150")
    self.title ("ChessCam Admin")

    # keeps track of background process
    self.camera_process = None

    # start button
    self.start_button = customtkinter.CTkButton(self, text='Start gjenkjenning', command=self.start_camera)
    self.start_button.pack(padx=20, pady=20)
    
    # stop button
    self.stop_button = customtkinter.CTkButton(self, text='Stopp kamera', command=self.stop_camera)
    self.stop_button.pack(padx=20, pady=0)

  def start_camera(self):
    # .poll() checks if the process is already running, stops us from opening 5 cameras for example
    if self.camera_process is None or self.camera_process.poll() is not None:
      print("Kamera starter")
      # this does the same as typing 'python main.py' in the terminal
      self.camera_process = subprocess.Popen(['python', 'main.py'])
    else:
      print("Kamera kjører allerede")

  def stop_camera(self):
    # if a process exists and is currently running
    if self.camera_process is not None and self.camera_process.poll() is None:
      print("Stopper kamera")
      self.camera_process.terminate()
      self.camera_process = None
    else:
      print("Kamera kjører ikke")

app = App()
app.mainloop()