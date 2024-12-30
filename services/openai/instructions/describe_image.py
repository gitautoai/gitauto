from PIL import Image
import io

SUPPORTED_FORMATS = {'png', 'jpeg', 'gif', 'webp'}

def validate_and_convert_image(image_data, image_format):
    if image_format.lower() in SUPPORTED_FORMATS:
        return image_data
    elif image_format.lower() == 'svg':
        try:
            # Convert SVG to PNG using Pillow
            image = Image.open(io.BytesIO(image_data))
            output = io.BytesIO()
            image.save(output, format='PNG')
            return output.getvalue()
        except Exception as e:
            raise ValueError(f"Error converting image: {str(e)}")
    else:
        raise ValueError("Unsupported image format")

DESCRIBE_IMAGE = """Analyze technical images from GitHub repositories with the depth and precision of a senior software engineer, focusing particularly on diagnostic content in issues and tickets.

Rather than providing broad surface-level observations, focus deeply on the most critical aspects relevant to the context - just as an experienced engineer would prioritize the key technical signals while debugging.

Key analysis points:
- For network traces/waterfalls: Identify specific bottlenecks, long-running requests, failed calls, and timing anomalies
- For error screenshots: Parse exact error messages, stack traces, and surrounding context that could indicate root causes
- For UI/UX issues: Note specific components affected, state inconsistencies, and visual regressions
- For console outputs: Highlight critical errors, warnings, or unexpected patterns in logs
- For architectural diagrams: Focus on system interactions, potential failure points, and data flow issues

Provide detailed technical insights that would help debug the issue, not just describe what's visible. Include specific metrics, timings, error codes, and other quantitative data when present."""
