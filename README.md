**Warning: This project contains AI-generated code. Please review and test carefully.**

This project is intended to generate layered QR codes that can be used to share secrets among a group of trusted friends. The secret is revealed only when a certain number of layers are combined, ensuring that no single person can access it alone. This can be used for games or as a dead-man switch.

# Visual QR Code Layer Generator

This project generates layered PNG images based on the principles of visual cryptography applied to QR codes. When a specific number of these layers (k) are stacked, they reveal the original QR code. Structural elements of the QR code are preserved across all layers, while data modules are distributed across the layers such that k layers are needed to reconstruct the black modules.

## Features

*   Encodes input data into a standard QR code.
*   Generates 'n' transparent PNG layers.
*   Requires 'k' out of 'n' layers to be stacked to reveal the QR code.
*   Identifies and preserves structural QR components (finder patterns, timing patterns, alignment patterns, format/version info) across all layers.
*   Distributes data/ECC modules according to the (k, n) threshold scheme.
*   Uses the `qrcode` and `Pillow` libraries.

## Setup

1.  **Create and activate a virtual environment:**
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows use `venv\Scripts\activate`
    ```

2.  **Install dependencies:**
    ```bash
    pip install --upgrade pip
    pip install qrcode[pil]
    ```

## Usage

The `generator.py` script contains the core logic and an example usage block.

1.  **Modify Parameters (Optional):**
    Open `generator.py` and adjust the parameters within the `if __name__ == '__main__':` block:
    *   `data_to_encode`: The string data you want to encode.
    *   `num_layers`: Total number of layers to generate (n).
    *   `required_layers`: Number of layers needed to reconstruct the QR code (k).
    *   `output_directory`: Folder where the layer images will be saved.
    *   `file_prefix`: Prefix for the output image filenames.
    *   `module_pixel_size`: Size of each QR code module in pixels.
    *   `quiet_zone_size`: Width of the border around the QR code (in modules).

2.  **Run the script:**
    ```bash
    python generator.py
    ```

3.  **Output:**
    The script will print the QR code version used and the progress. The generated PNG layer images will be saved in the specified `output_directory` (default is `output_layers/`).

## How it Works

1.  A standard QR code is generated for the input data.
2.  The script identifies which modules are structural (finders, alignment, timing, etc.) and which are data/ECC modules.
3.  'n' transparent layers are created.
4.  **Structural Modules:** If a structural module is black in the original QR code, it's drawn as black on *all* 'n' layers. If it's white, it remains transparent on all layers.
5.  **Data/ECC Modules:** If a data module is black in the original QR code, it's drawn as black on a randomly selected subset of exactly `n - k + 1` layers. This ensures that when any 'k' layers are combined, this module appears black. If it's white, it remains transparent on all layers.
6.  The layers are saved as individual PNG files.

## Dependencies

*   [qrcode](https://pypi.org/project/qrcode/) (with PIL support)
*   [Pillow](https://pypi.org/project/Pillow/)

## TODO / Potential Improvements

*   Implement more robust `is_structural` detection, potentially using the QR code standard specifications directly instead of heuristics, especially for higher versions and different mask patterns.
*   Add options for different error correction levels.
*   Explore different visual cryptography schemes.
*   Add command-line arguments for easier configuration.
