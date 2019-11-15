import sys
import threading
import queue
import numpy as np
import scipy as sp
import scipy.signal
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import pyaudio
import tkinter


f_sampling = 44100
mic_chunk = 2**11
mic_readings = []
mic_last = 0
mic_calibration = 1
remote_offset = 0
duration = 10.0
sample_len = int(f_sampling * duration)
t = np.arange(sample_len)

stereo_signal = np.zeros([sample_len, 2], dtype=np.float32)

index = 0



def sound_callback(in_data, frame_count, time_info, status):
    global index
    global mic_readings
    global mic_last
    global remote_offset
    cut_index = (index + frame_count) if (index + frame_count) <= sample_len else sample_len
    data = stereo_signal[index:cut_index, :] 
    if cut_index != sample_len:
        index = cut_index
    else:
        index = frame_count - len(data)
        data = np.concatenate([np.asarray(data), np.asarray(stereo_signal[0:index, :])])
    
    mic_data = np.frombuffer(in_data, dtype=np.float32)[1::2].copy() #ONLY LEFT CHANNEL
    mic_data -= np.average(mic_data)
    peak = np.average(np.abs(mic_data))*2 * 1000
    mic_readings.append(peak)
    if len(mic_readings) == 6:
        mic_last = np.average(mic_readings)
        mic_fl = mic_last / mic_calibration if mic_calibration != 0 else mic_last
        remote_offset = mic_fl * 3 - 1.5
        mic_readings = []

    return (data, pyaudio.paContinue)

def mic_callback(in_data, frame_count, time_info, status):
    pass

class MainWindow(tkinter.Frame):
    def __init__(self, root):
        tkinter.Frame.__init__(self, root)
        self.root = root
        root.title("Noche de los Museos")
        root.geometry("1000x630")
        root.protocol('WM_DELETE_WINDOW', self.close_fn)
        self.bind('<Return>', self.updateGenerator)
        
        self.samples_1 = np.zeros(sample_len)
        self.samples_2 = np.zeros(sample_len)
        self.is_playing_1 = False
        self.is_playing_2 = False

        self.remote = False
        

        self.p_audio = pyaudio.PyAudio()
        self.stream = self.p_audio.open(format=pyaudio.paFloat32, channels=2, rate=f_sampling, \
            output=True, input=True, stream_callback=sound_callback, frames_per_buffer=mic_chunk)
        self.stream.start_stream()

        vcmd = (self.register(self.onFloatValidate),'%d', '%i', '%P', '%s', '%S', '%v', '%V', '%W')

        tkinter.Label(self, text = 'Vibración del Agua:').grid(row = 0)

        self.button_toggle_1 = tkinter.Button(self, text='Activar', command=self.press_button_toggle_1)
        self.button_toggle_1.grid(row=1)

        tkinter.Label(self, text = 'Frecuencia (Hz):').grid(row = 1, column=1)
        self.freq_1_entry_text = tkinter.StringVar()
        self.freq_1_entry = tkinter.Entry(self, validate='key', validatecommand=vcmd, \
                                            textvariable=self.freq_1_entry_text)
        self.freq_1_entry.grid(row=1, column=2)
        self.freq_1_entry_text.set('25')
        self.freq_1_update = tkinter.Button(self, text='Aplicar', command=self.updateGenerator)
        self.freq_1_update.grid(row=1, column=3)
        self.freq_1_up = tkinter.Button(self, text='↑', command=self.freq_1_up_command)
        self.freq_1_up.grid(row=1, column=4)
        self.freq_1_down = tkinter.Button(self, text='↓', command=self.freq_1_down_command)
        self.freq_1_down.grid(row=1, column=5)

        tkinter.Label(self, text = 'Fase:').grid(row=1, column=6)
        self.phase_1_slider = tkinter.Scale(self, from_=0, to=2*np.pi, resolution=0.01, \
                                            orient=tkinter.HORIZONTAL, command=self.updateGenerator)
        self.phase_1_slider.grid(row=1, column=7)

        tkinter.Label(self, text = 'Intensidad:').grid(row = 1, column=8)
        self.intensity_1_slider = tkinter.Scale(self, from_=0, to=1, resolution=0.01, \
                                            orient=tkinter.HORIZONTAL, command=self.updateGenerator)
        self.intensity_1_slider.grid(row=1, column=9)
        self.intensity_1_slider.set(1)
        


        tkinter.Label(self, text = 'Luz Estroboscópica:').grid(row = 2)

        self.button_toggle_2 = tkinter.Button(self, text='Activar', command=self.press_button_toggle_2)
        self.button_toggle_2.grid(row=3)

        tkinter.Label(self, text = 'Frecuencia (Hz):').grid(row = 3, column=1)
        self.freq_2_entry_text = tkinter.StringVar()
        self.freq_2_entry = tkinter.Entry(self, validate='key', validatecommand=vcmd, \
                                            textvariable=self.freq_2_entry_text)
        self.freq_2_entry.grid(row=3, column=2)
        self.freq_2_entry_text.set('25')
        self.freq_1_update = tkinter.Button(self, text='Aplicar', command=self.updateGenerator)
        self.freq_1_update.grid(row=3, column=3)
        self.freq_2_up = tkinter.Button(self, text='↑', command=self.freq_2_up_command)
        self.freq_2_up.grid(row=3, column=4)
        self.freq_2_down = tkinter.Button(self, text='↓', command=self.freq_2_down_command)
        self.freq_2_down.grid(row=3, column=5)

        tkinter.Label(self, text = 'Fase:').grid(row=3, column=6)
        self.phase_2_slider = tkinter.Scale(self, from_=0, to=2*np.pi, resolution=0.01, \
                                            orient=tkinter.HORIZONTAL, command=self.updateGenerator)
        self.phase_2_slider.grid(row=3, column=7)

        tkinter.Label(self, text = 'Intensidad:').grid(row = 3, column=8)
        self.intensity_2_slider = tkinter.Scale(self, from_=0, to=1, resolution=0.01, \
                                            orient=tkinter.HORIZONTAL, command=self.updateGenerator)
        self.intensity_2_slider.grid(row=3, column=9)
        self.intensity_2_slider.set(1)

        self.defaults_button_25 = tkinter.Button(self, text="Default 25Hz", command=self.default_config_25)
        self.defaults_button_25.grid(column=10, row=1)

        self.defaults_button_30 = tkinter.Button(self, text="Default 30Hz", command=self.default_config_30)
        self.defaults_button_30.grid(column=10, row=3)

        self.remote_control_calibration = tkinter.Button(self, text='Calibrar', command=self.remote_calibration)
        self.remote_control_calibration.grid(row=1, column=11)

        self.remote_control_button = tkinter.Button(self, text='Remoto', command=self.toggle_remote, relief="raised")
        self.remote_control_button.grid(row=3, column=11)
        #if self.remote_port is None:
        #    self.remote_control_button.config(state='disabled')
        self.remote_control_offset = tkinter.Label(self, text='25')
        self.remote_control_offset.grid(row = 3, column=12)



        
        self.plot_fig = plt.Figure(figsize=(10,5), dpi=100)
        self.plot_ax1 = self.plot_fig.add_subplot(311)
        self.plot_samples_1 = self.plot_ax1.plot(t, self.samples_1)[0]
        self.plot_ax1.set_ylim(-1.1, 1.1)
        self.plot_ax1.set_xlim(0, t[-1] * 0.01)
        self.plot_ax1.xaxis.set_ticklabels([])
        self.plot_ax1.set_ylabel('Agua')
        self.plot_ax2 = self.plot_fig.add_subplot(312)
        self.plot_samples_2 = self.plot_ax2.plot(t, self.samples_2)[0]
        self.plot_ax2.set_ylim(-0.1, 1.1)
        self.plot_ax2.set_xlim(0, t[-1] * 0.01)
        self.plot_ax2.xaxis.set_ticklabels([])
        self.plot_ax2.set_ylabel('Luz')
        self.plot_ax3 = self.plot_fig.add_subplot(313)
        self.plot_samples_3 = self.plot_ax3.plot(t, self.samples_1 * self.samples_2)[0]
        self.plot_ax3.set_ylim(-1.1, 1.1)
        self.plot_ax3.set_xlim(0, t[-1] * 0.01)
        self.plot_ax3.set_ylabel('Superposición')
        self.plot_ax3.set_xlabel('t')

        self.plot_canvas = FigureCanvasTkAgg(self.plot_fig, master=self)
        self.plot_canvas.draw()
        self.plot_canvas.get_tk_widget().grid(row=5, columnspan=13)

        #self.after(200, self.remote_update)

    def onFloatValidate(self, d, i, P, s, S, v, V, W):
        try:
            if P == '':
                return True
            float(P)
            return True
        except ValueError:
            self.bell()
            return False

    def freq_1_up_command(self):
        self.freq_1_entry_text.set(str(round(float(self.freq_1_entry_text.get()) + 0.1, 2)))
        self.updateGenerator()

    def freq_1_down_command(self):
        f = float(self.freq_1_entry_text.get())
        if f >= 0.1:
            self.freq_1_entry_text.set(str(f - 0.1))
        else:
            self.freq_1_entry_text.set(0)
        self.updateGenerator()

    def freq_2_up_command(self):
        self.freq_2_entry_text.set(str(round(float(self.freq_2_entry_text.get()) + 0.1, 2)))
        self.updateGenerator()

    def freq_2_down_command(self):
        f = float(self.freq_2_entry_text.get())
        if f >= 0.1:
            self.freq_2_entry_text.set(str(f - 0.1))
        else:
            self.freq_2_entry_text.set(0)
        self.updateGenerator()

    def updateGenerator(self, *argv):
        t1 = self.freq_1_entry_text.get()
        if t1 == '' or float(t1) < 0:
            self.freq_1_entry_text.set('0')
        t2 = self.freq_2_entry_text.get()
        if t2 == '' or float(t2) < 0:
            self.freq_2_entry_text.set('0')

        f2 = float(self.freq_2_entry_text.get())
        if self.remote:
            f2 += remote_offset
            if f2 < 0:
                f2 = 0
        self.remote_control_offset.config(text='%.2f' % round(f2, 2))

        if self.is_playing_1:
            self.samples_1 = self.create_sin(float(self.freq_1_entry_text.get()), \
                                                self.phase_1_slider.get(), \
                                                self.intensity_1_slider.get())
        else:
            self.samples_1 = np.zeros(sample_len)
        
        if self.is_playing_2:
            self.samples_2 = self.create_square(f2, \
                                                self.phase_2_slider.get(), \
                                                self.intensity_2_slider.get())
        else:
            self.samples_2 = np.zeros(sample_len)

        stereo_signal[:, 0] = self.samples_1[:] #1 for right speaker, 0 for left
        stereo_signal[:, 1] = self.samples_2[:] #1 for right speaker, 0 for left

        self.plot_samples_1.set_ydata(self.samples_1)
        self.plot_samples_2.set_ydata(self.samples_2)
        self.plot_samples_3.set_ydata(self.samples_1 * self.samples_2)
        self.plot_canvas.draw()
        self.plot_canvas.flush_events()

    def create_sin(self, f=25, phase=0, v=1):
        return (np.sin(2 * np.pi * t * f / f_sampling + phase)).astype(np.float32) * v

    def create_square(self, f=25, phase=0, v=1):
        return (sp.signal.square(2 * np.pi * t * f / f_sampling + phase) + 1).astype(np.float32) * v/2

    def press_button_toggle_1(self):
        if self.is_playing_1:
            self.is_playing_1 = False
            self.button_toggle_1.config(text="Activar")
        else:
            self.is_playing_1 = True
            self.button_toggle_1.config(text="Desactivar")
        self.updateGenerator()

    def press_button_toggle_2(self):
        if self.is_playing_2:
            self.is_playing_2 = False
            self.button_toggle_2.config(text="Activar")
        else:
            self.is_playing_2 = True
            self.button_toggle_2.config(text="Desactivar")
        self.updateGenerator()

    def default_config_25(self):
        self.freq_1_entry_text.set(25)
        self.freq_2_entry_text.set(25)
        self.phase_1_slider.set(0)
        self.phase_2_slider.set(0)
        self.intensity_1_slider.set(1)
        self.intensity_2_slider.set(1)
        self.is_playing_1 = True
        self.button_toggle_1.config(text="Desactivar")
        self.is_playing_2 = True
        self.button_toggle_2.config(text="Desactivar")
        self.updateGenerator()
    
    def default_config_30(self):
        self.freq_1_entry_text.set(30)
        self.freq_2_entry_text.set(30)
        self.phase_1_slider.set(0)
        self.phase_2_slider.set(0)
        self.intensity_1_slider.set(1)
        self.intensity_2_slider.set(1)
        self.is_playing_1 = True
        self.button_toggle_1.config(text="Desactivar")
        self.is_playing_2 = True
        self.button_toggle_2.config(text="Desactivar")
        self.updateGenerator()

    def toggle_remote(self):
        if self.remote:
            self.remote_control_button.config(relief='raised')
            self.remote = False
            self.freq_2_entry.config(fg='black')
        else:
            self.remote_control_button.config(relief='sunken')
            self.remote = True
            self.after(300, self.remote_update)
            self.freq_2_entry.config(fg='red')
        self.updateGenerator()

    def remote_update(self):
        self.updateGenerator()
        if self.remote:
            self.after(300, self.remote_update)
            
    def remote_calibration(self):
        global mic_calibration
        mic_calibration = mic_last
    
    def close_fn(self):
        self.stream.stop_stream()
        self.stream.close()
        self.p_audio.terminate()
        self.root.destroy()

def main():
    root = tkinter.Tk()
    MainWindow(root).pack(fill="both", expand=True)
    root.mainloop()

if __name__ == '__main__':
    main()