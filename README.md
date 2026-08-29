# AI Room Generator

Isolated MVP generator for pixel-perfect PNG schemes of 2D game rooms.

The project is standalone and does not touch n8n, n8n credentials, existing workflows, reverse proxy settings, or production services.

## What It Does

- Generates room specifications as compact semantic JSON.
- Renders deterministic PNG maps where `1 pixel = 1 game meter`.
- Uses only whitelisted tile colors from one central config.
- Validates geometry, object constraints, connectivity, bounds, collisions, PNG dimensions, and PNG color whitelist.
- Produces 20 different rooms with one command.
- Provides a small local web UI.

## Architecture

```text
User parameters
  -> deterministic room generator
  -> deterministic validator
  -> local auto-fix
  -> PNG renderer
  -> pixel whitelist validator
  -> output/*.png + output/*.json + generation_report.json
```

Optional OpenAI support is isolated in `roomgen/openai_client.py`. The MVP does not call OpenAI by default, which keeps token usage at zero during local tests.

## Install

No third-party packages are required for the deterministic MVP.

```bash
cd ai-room-generator
python --version
```

Optional:

```bash
copy .env.example .env
```

Then put your key into `.env` or export it:

```env
OPENAI_API_KEY=your_key_here
```

Do not copy keys from n8n credentials. This prototype uses only its own environment variable.

## Generate One Or More Rooms

```bash
python generate.py --rooms 1 --width 80 --height 40
```

## Generate 20 Rooms

```bash
python generate.py --rooms 20
```

Files are written to:

```text
output/
  room_001.png
  room_001.json
  ...
  room_020.png
  room_020.json
  generation_report.json
```

## Validate Output

```bash
python validate.py output/
```

The validator checks:

- room dimensions;
- allowed object types;
- door dimensions: `1x3`;
- ladder width: `1`;
- platform height: `1`;
- decor sizes: `1x1`, `1x2`, `2x1`, `2x2`, `3x3`, `4x3`;
- enemy size: `1x1`;
- bounds;
- collisions;
- doors exist;
- ladders/platforms exist;
- connectivity by deterministic flood fill;
- PNG dimensions;
- PNG colors against whitelist.

## Web UI

```bash
python server.py
```

Open:

```text
http://127.0.0.1:8010
```

The page lets you set:

- Room Width
- Room Height
- Doors
- Enemies
- Difficulty
- Platform Density
- Decor Density
- Layout Type
- Number of Rooms
- Seed

After generation it shows previews, validation status, generation time, and download links for PNG/JSON.

## PNG Format

- PNG only.
- No JPEG.
- No antialiasing.
- No resizing.
- No interpolation.
- Truecolor RGB.
- `width x height` pixels.
- Each object is rendered directly from discrete grid rectangles.

## JSON Format

Each room JSON contains:

```json
{
  "room_id": 1,
  "width": 80,
  "height": 40,
  "seed": 13354,
  "layout_type": "industrial",
  "objects": [
    { "type": "wall", "x": 0, "y": 38, "w": 80, "h": 2 },
    { "type": "platform", "x": 15, "y": 25, "w": 12, "h": 1 },
    { "type": "door", "x": 1, "y": 35, "w": 1, "h": 3 }
  ]
}
```

## Colors

All colors live in `roomgen/config.py`:

```python
PALETTE = {
    "EMPTY": (255, 255, 255),
    "WALL": (0, 0, 0),
    "PLATFORM": (79, 184, 255),
    "LADDER": (255, 220, 48),
    "DOOR": (255, 72, 72),
    "DECOR": (255, 150, 170),
    "ENEMY": (220, 30, 30),
}
```

Important: these are demo placeholders. The screenshots are not reliable enough to confirm production RGB values. Before connecting the output to the real level constructor, confirm exact RGB values and update only `roomgen/config.py`.

## Change Rules

Geometry rules are centralized in:

- `roomgen/config.py`
- `roomgen/validator.py`
- `roomgen/generator.py`

## Change AI Model

Optional OpenAI calls use:

```env
OPENAI_MODEL=gpt-4o-mini
```

The deterministic MVP does not need the model and does not spend tokens.

## Cost Estimate

Default deterministic generation cost:

```text
estimated_openai_cost = 0.0
```

If optional AI generation is enabled later, keep the flow compact:

```text
compact prompt -> structured JSON -> local validator -> local renderer
```

Never send the final PNG or a full pixel matrix back to the model.

## Limitations

- Exact production RGB colors need confirmation.
- Unity integration is represented as a contract, not as a Unity plugin.
- The default MVP uses deterministic procedural layouts. The OpenAI client is isolated and optional.

## Unity / Level Constructor Contract

```text
Generator
  -> room_###.png
  -> Level Constructor
  -> Unity
```

The PNG is the importable tile map. The JSON is the semantic debugging representation.

## Tests

```bash
python -m unittest discover -s tests
```

The test suite includes:

- colors;
- door dimensions;
- ladder dimensions;
- platform dimensions;
- decor dimensions;
- enemy dimensions;
- bounds;
- collisions;
- connectivity;
- PNG colors;
- PNG dimensions;
- generate 20 rooms and assert all valid.

