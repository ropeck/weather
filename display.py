# -*- coding:utf-8 -*-

from PIL import Image, ImageDraw, ImageFont

font_choice = 7
if font_choice == 1:
    project_font = "font/Architects_Daughter/ArchitectsDaughter-Regular.ttf"
elif font_choice == 2:
    project_font = "font/Inconsolata/static/Inconsolata-SemiBold.ttf"
elif font_choice == 3:
    project_font = "font/Comfortaa/static/Comfortaa-Light.ttf"
elif font_choice == 4:
    project_font = "font/Open_Sans/OpenSans-SemiBold.ttf"
elif font_choice == 5:
    project_font = "font/Roboto/Roboto-Regular.ttf"
elif font_choice == 6:
    project_font = "font/Roboto_Slab/static/RobotoSlab-Regular.ttf"
elif font_choice == 7:
    project_font = "font/ubuntu-font-family-0.83/Ubuntu-B.ttf"
else:
    project_font = "font/Open_Sans/OpenSans-SemiBold.ttf"

try:
    font8 = ImageFont.truetype(project_font, 8)
except OSError:
    project_font = "arial.ttf"
print(project_font)

font8 = ImageFont.truetype(project_font, 8)
font12 = ImageFont.truetype(project_font, 12)
font14 = ImageFont.truetype(project_font, 14)
font16 = ImageFont.truetype(project_font, 16)
font24 = ImageFont.truetype(project_font, 24)
font48 = ImageFont.truetype(project_font, 48)
font96 = ImageFont.truetype(project_font, 96)


class Display:
    def __init__(self):
        self.im_black = Image.new('1', (600, 448), 255)
        self.im_black = Image.new('RGB', (600, 448), 0xffffff)
        self.im_red = Image.new('1', (600, 448), 255)
        self.draw_black = ImageDraw.Draw(self.im_black)
        self.draw_red = ImageDraw.Draw(self.im_red)
        self.draw_red = self.draw_black

    def draw_circle(self, x, y, r, c):
        if c == "b":
            self.draw_black.ellipse((x - r, y - r, x + r, y + r), fill=0)
        else:
            self.draw_red.ellipse((x - r, y - r, x + r, y + r), fill=0)

    def draw_icon(self, x, y, c, l, h, icon):
        try:
            print("draw_icon: {}.png".format(icon))
            im_icon = Image.open("icons/" + icon + ".png")
        #im_icon = im_icon.convert("LA")
            im_icon = im_icon.resize((l, h))
            self.im_black.paste(im_icon, (x, y), im_icon)
        except Exception as e:
            print(str(e))
            self.im_black.text((x, y), "not found: {}".format(icon), fill="red", font=font48)