import argparse
import os
from layered_qr.generator import generate_visual_layered_qrs

def main():
    parser = argparse.ArgumentParser(description='Generate visually stackable QR code layers.')
    parser.add_argument('text', type=str, help='The text content to encode in the final QR code.')
    parser.add_argument('-n', '--total_pieces', type=int, required=True, help='Total number of image layers to generate (n).')
    parser.add_argument('-k', '--required_pieces', type=int, required=True, help='Number of layers that must be stacked to form the QR code (k).')
    parser.add_argument('-o', '--output_dir', type=str, default='output_visual', help='Directory to save the generated QR code layer images.')
    parser.add_argument('--prefix', type=str, default='qr_layer_', help='Filename prefix for the output layer images.')
    parser.add_argument('--box_size', type=int, default=10, help='Size of each QR code module/box in pixels.')
    parser.add_argument('--border', type=int, default=4, help='Width of the quiet zone border around the QR code (in modules).')


    args = parser.parse_args()

    if args.required_pieces > args.total_pieces:
        print("Error: Required pieces (k) cannot be greater than total pieces (n).")
        return
    if args.required_pieces <= 0 or args.total_pieces <= 0:
        print("Error: Number of pieces must be positive.")
        return
    if args.required_pieces < 1: # Need at least 1 layer to make it black
        print("Error: Required pieces (k) must be at least 1.")
        return

    # Ensure output directory exists
    os.makedirs(args.output_dir, exist_ok=True)

    print(f"Encoding text: '{args.text}'")
    print(f"Generating {args.total_pieces} visual layers, requiring {args.required_pieces} to form the QR code.")
    print(f"Saving images to: {args.output_dir}")

    try:
        generate_visual_layered_qrs(
            data=args.text,
            n=args.total_pieces,
            k=args.required_pieces,
            output_dir=args.output_dir,
            filename_prefix=args.prefix,
            box_size=args.box_size,
            border=args.border
        )
        print(f"Successfully generated {args.total_pieces} QR code layer images.")
    except Exception as e:
        print(f"An error occurred: {e}")
        # Consider adding more detailed error logging or traceback here
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
