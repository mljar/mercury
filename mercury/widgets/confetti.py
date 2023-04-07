from IPython.display import display, HTML


def Confetti():
    display(
        HTML(
            """
    <script type="module">import confetti from 'https://cdn.skypack.dev/canvas-confetti'; 
    confetti({
    particleCount: 300, 
    angle: 90, 
    spread: 180,
    decay: 0.9,
    startVelocity: 40,
    origin: {
        x: 0.5,
        y: 0.5
    }
    });
    
    </script>
    """
        )
    )
