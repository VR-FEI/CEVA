def custom_resize(width, height, canvas_width, canvas_height):
    aspect_ratio = width / height
    if aspect_ratio > 1:
        # If the image is wider than it is tall
        new_width = canvas_width
        new_height = round(canvas_width / aspect_ratio)
    else:
        # If the image is taller than it is wide
        new_height = canvas_height
        new_width = round(canvas_height * aspect_ratio)

    return (new_width, new_height)