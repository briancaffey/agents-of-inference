# agents-of-inference

## TODO

- Add agent/node for frame interpolation with ffmpeg

```
ffmpeg -i output/1718300379/final.mp4 -crf 10 -vf "minterpolate=fps=14:mi_mode=mci:mc_mode=aobmc:me_mode=bidir:vsbmc=1" output/1718300379/final.14fps.mp4
```

```python
import ffmpeg

input_file = 'input.mp4'
output_file = 'output.14fps.mp4'

(
    ffmpeg
   .input(input_file)
   .output(output_file, crf=10, vf="minterpolate=fps=14:mi_mode=mci:mc_mode=aobmc:me_mode=bidir:vsbmc=1")
   .run()
)

```


- Add service for ChatTTS
