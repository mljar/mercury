class SlidesThemes:
    @staticmethod
    def nbconvert_options(format):
        theme = format.get("theme", "white")

        if theme == "black":
            return [
                "--SlidesExporter.reveal_theme=black",
                "--SlidesExporter.theme=dark",
            ]
        elif theme == "white":
            return [
                "--SlidesExporter.reveal_theme=white",
                "--SlidesExporter.theme=light",
            ]
        elif theme == "league":
            return [
                "--SlidesExporter.reveal_theme=league",
                "--SlidesExporter.theme=dark",
            ]
        elif theme == "sky":
            return [
                "--SlidesExporter.reveal_theme=sky",
                "--SlidesExporter.theme=light",
            ]
        elif theme == "beige":
            return [
                "--SlidesExporter.reveal_theme=beige",
                "--SlidesExporter.theme=light",
            ]
        elif theme == "simple":
            return [
                "--SlidesExporter.reveal_theme=simple",
                "--SlidesExporter.theme=light",
            ]
        elif theme == "serif":
            return [
                "--SlidesExporter.reveal_theme=serif",
                "--SlidesExporter.theme=light",
            ]
        elif theme == "blood":
            return [
                "--SlidesExporter.reveal_theme=blood",
                "--SlidesExporter.theme=dark",
            ]
        elif theme == "night":
            return [
                "--SlidesExporter.reveal_theme=night",
                "--SlidesExporter.theme=dark",
            ]
        elif theme == "moon":
            return [
                "--SlidesExporter.reveal_theme=moon",
                "--SlidesExporter.theme=dark",
            ]
        elif theme == "solarized":
            return [
                "--SlidesExporter.reveal_theme=solarized",
                "--SlidesExporter.theme=light",
            ]

        return []

    @staticmethod
    def additional_css(format):
        theme = format.get("theme", "white")

        if theme == "black":
            return """\n<style type="text/css">
.reveal * {
    color: rgb(255, 255, 255);
    font-family: "Source Sans Pro", Helvetica, sans-serif;
}
</style>"""
        elif theme == "white":
            return """\n<style type="text/css">
.reveal * {
    color: rgb(34, 34, 34);
    font-family: "Source Sans Pro", Helvetica, sans-serif;
}
</style>"""
        elif theme == "league":
            return """\n<style type="text/css">
.reveal * {
    color: rgb(238, 238, 238);
    font-family: "Lato", sans-serif;
}
</style>"""
        elif theme == "sky":
            return """\n<style type="text/css">
.reveal * {
    color: rgb(51, 51, 51);
    font-family: "Open Sans", sans-serif;
}
</style>"""
        elif theme == "beige":
            return """\n<style type="text/css">
.reveal * {
    color: rgb(51, 51, 51);
    font-family: "Lato", sans-serif;
}
</style>"""
        elif theme == "simple":
            return """\n<style type="text/css">
.reveal * {
    color: rgb(0, 0, 0);
    font-family: "Lato", sans-serif;
}
</style>"""
        elif theme == "serif":
            return """\n<style type="text/css">
.reveal * {
    color: rgb(0, 0, 0);
    font-family: "Palatino Linotype", "Book Antiqua", Palatino, FreeSerif, serif;
}
</style>"""
        elif theme == "blood":
            return """\n<style type="text/css">
.reveal * {
    color: rgb(238, 238, 238);
    font-family: Ubuntu, "sans-serif";  
}
</style>"""
        elif theme == "night":
            return """\n<style type="text/css">
.reveal * {
    color: rgb(238, 238, 238);
    font-family: "Open Sans", sans-serif;  
}
</style>"""
        elif theme == "moon":
            return """\n<style type="text/css">
.reveal * {
    rgb(147, 161, 161);
    font-family: "Lato", sans-serif;
}
</style>"""
        elif theme == "solarized":
            return """\n<style type="text/css">
.reveal * {
    color: rgb(101, 123, 131);
    font-family: "Lato", sans-serif;
}
</style>"""

        return ""
