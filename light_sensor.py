#!/usr/bin/python3
import board
import digitalio
import time

l = digitalio.DigitalInOut(board.D26)
while True:
  l.direction=digitalio.Direction.OUTPUT
  l.value=False
  time.sleep(0.1)
  l.direction=digitalio.Direction.INPUT
  t=time.time()
  while not l.value:
    time.sleep(0.001)
  d = time.time()-t
  v = 'off'
  if d < 0.3:
      v = 'on'
  print(v, l.value, time.time()-t)
  
