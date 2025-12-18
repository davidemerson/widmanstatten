# Procedural Meteorite Pattern Generator

This project generates large-format, purely vector, procedurally generated meteorite-like surface patterns and outputs them as PDF files suitable for print, CNC, laser, or further vector processing.

The algorithm was developed by studying a slice of the Muonionalusta meteorite, discovered in northern Sweden in 1906. Muonionalusta is an iron-nickel meteorite that exhibits a Widmanstätten pattern when etched, revealing interlocking crystalline phases formed by extremely slow cooling over millions of years.

This generator models the statistical and structural properties visible in etched meteorite slices: - dominant crystallographic directions
- layered cross-hatching
- imperfect, double-etched strokes
- missing material and discontinuities
- large-scale grain regions with local variation

The result is a pattern that looks geologic and crystalline rather than
decorative or algorithmic.

## Output Characteristics

-   Arbitrary size PDF (limited only by memory/time)
-   No rasterization, no textures, no images
-   Every run produces a unique pattern by default
-   Optional deterministic regeneration via seed

## High-Level Method

The image is synthesized as the superposition of several independent line families, each representing a dominant crystallographic direction.

Each family is generated using the following components:

### 1. Directional Angle Mixture

A small set of dominant line orientations is defined (e.g. \~45°, \~135°, minor orthogonal components).\ Each stroke family samples from a weighted angular distribution with tight variance, producing strong directional bias without mechanical regularity.

### 2. Parallel Stroke Fields

For each direction: - an infinite set of nearly parallel lines is generated - spacing is randomized using a log-normal distribution - lines overshoot the page and are clipped implicitly

This mimics the irregular lamella spacing seen in etched iron--nickel alloys.

### 3. Grain Modulation Field

A low-frequency fractal noise field (FBM over value noise) is evaluated across the surface.

This grain field modulates: - stroke width - stroke opacity - dropout probability - ghost-stroke offsets

This produces large-scale "crystal regions" where texture coherently shifts.

### 4. Stroke Imperfection

No line is perfectly straight: - lateral jitter is applied along the normal direction - jitter is smooth, not noisy, to avoid cartoon effects, additional "ghost strokes" are drawn nearby to simulate double-etching

### 5. Material Loss / Etch Gaps

Segments of strokes are randomly dropped based on local grain intensity, producing: broken lines, etched voids, and discontinuities characteristic of physical material removal

## Randomness and Reproducibility

By default: - Each run uses a cryptographically strong random seed - You will never get the same output twice unless you use the same seed.

For reproducibility: - You may supply an explicit `seed` - The seed used is printed after generation - Reusing the seed reproduces the pattern exactly

## File Naming

Generated PDFs are automatically timestamped using UTC:

    meteorite-YYYY-MM-DD-HH-MM-SS.SS.pdf

Example:

    meteorite-2025-12-18-14-03-22.17.pdf

## Usage

### Install dependencies

``` bash
pip install reportlab
```

### Generate a pattern

``` bash
python meteorite.py
```

The script will: - generate a new, unique pattern - write a timestamped PDF - print the output path and seed

### Deterministic regeneration

``` python
generate_meteorite_pdf(
    W=3000,
    H=1800,
    seed=123456789
)
```

## Coordinate System and Scale

PDF units are **points** (1/72 inch), but since the output is vector, you may treat units as arbitrary.

For example: - 36×24 inches → 2592×1728 points - Large architectural panels are feasible
