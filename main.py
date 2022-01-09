#coding=utf-8
import sys
import os
import time
import threading
import cv2
import pyprind


class CharFrame:
    ascii_char = "$@B%8&WM#*oahkbdpqwmZO0QLCJUYXzcvunxrjft/\|()1{}[]?-_+~<>i!lI;:,\"^`'. "

    # 像素映射到字符
    def pixelToChar(self, luminance):
        return self.ascii_char[int(luminance / 256 * len(self.ascii_char))]

    # 将普通帧转为 ASCII 字符帧
    def convert(self, img, limitSize=-1, fill=False, wrap=False):
        if limitSize != -1 and (img.shape[0] > limitSize[1] or img.shape[1] > limitSize[0]):
            img = cv2.resize(img, limitSize, interpolation=cv2.INTER_AREA)
        ascii_frame = ''
        blank = ''
        if fill:
            blank += ' ' * (limitSize[0] - img.shape[1])
        if wrap:
            blank += '\n'
        for i in range(img.shape[0]):
            for j in range(img.shape[1]):
                ascii_frame += self.pixelToChar(img[i, j])
            ascii_frame += blank
        return ascii_frame


class V2Char(CharFrame):
    charVideo = []
    timeInterval = 0.033

    def __init__(self, path):
        if path.endswith('txt'):
            self.load(path)
        else:
            self.genCharVideo(path)

    def genCharVideo(self, filepath):
        self.charVideo = []
        # 用opencv读取视频
        cap = cv2.VideoCapture(filepath)
        self.timeInterval = round(1 / cap.get(5), 3)
        nf = int(cap.get(7))
        print('Generate char video, please wait...')
        for i in pyprind.prog_bar(range(nf)):
            # 转换颜色空间，第二个参数是转换类型，cv2.COLOR_BGR2GRAY表示从BGR↔Gray
            rawFrame = cv2.cvtColor(cap.read()[1], cv2.COLOR_BGR2GRAY)
            frame = self.convert(rawFrame, os.get_terminal_size(), fill=True)
            self.charVideo.append(frame)
        cap.release()

    def export(self, filepath):
        if not self.charVideo:
            return
        with open(filepath, 'w') as f:
            for frame in self.charVideo:
                # 加一个换行符用以分隔每一帧
                f.write(frame + '\n')

    def load(self, filepath):
        self.charVideo = []
        # 一行即为一帧
        for i in open(filepath):
            self.charVideo.append(i[:-1])

    def play(self, stream=1):
        # Bug:
        # 光标定位转义编码不兼容 Windows
        if not self.charVideo:
            return
        if stream == 1 and os.isatty(sys.stdout.fileno()):
            self.streamOut = sys.stdout.write
            self.streamFlush = sys.stdout.flush
        elif stream == 2 and os.isatty(sys.stderr.fileno()):
            self.streamOut = sys.stderr.write
            self.streamFlush = sys.stderr.flush
        elif hasattr(stream, 'write'):
            self.streamOut = stream.write
            self.streamFlush = stream.flush
        breakflag = False

        def getChar():
            nonlocal breakflag
            try:
                # 若系统为 windows 则直接调用 msvcrt.getch()
                import msvcrt
            except ImportError:
                import termios
                import tty
                # 获得标准输入的文件描述符
                fd = sys.stdin.fileno()
                # 保存标准输入的属性
                old_settings = termios.tcgetattr(fd)
                try:
                    # 设置标准输入为原始模式
                    tty.setraw(sys.stdin.fileno())
                    # 读取一个字符
                    ch = sys.stdin.read(1)
                finally:
                    # 恢复标准输入为原来的属性
                    termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
                if ch:
                    breakflag = True
            else:
                if msvcrt.getch():
                    breakflag = True

        # 创建线程
        getchar = threading.Thread(target=getChar)
        # 设置为守护线程
        getchar.daemon = True
        # 启动守护线程
        getchar.start()
        # 输出的字符画行数
        rows = len(self.charVideo[0]) // os.get_terminal_size()[0]
        for frame in self.charVideo:
            # 接收到输入则退出循环
            if breakflag:
                break
            self.streamOut(frame)
            self.streamFlush()
            time.sleep(self.timeInterval)
            # 共 rows 行，光标上移 rows-1 行回到开始处
            self.streamOut('\033[{}A\r'.format(rows - 1))
        # 光标下移 rows-1 行到最后一行，清空最后一行
        self.streamOut('\033[{}B\033[K'.format(rows - 1))
        # 清空最后一帧的所有行（从倒数第二行起）
        for i in range(rows - 1):
            # 光标上移一行
            self.streamOut('\033[1A')
            # 清空光标所在行
            self.streamOut('\r\033[K')
        if breakflag:
            self.streamOut('User interrupt!\n')
        else:
            self.streamOut('Finished!\n')


if __name__ == "__main__":
    v2char = V2Char('./vedio.mp4')
    v2char.play()

