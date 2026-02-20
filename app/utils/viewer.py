from PIL import Image, ImageDraw
from pathlib import Path
import logging
from dataclasses import dataclass
from typing import Dict, Tuple, Optional, List
from functools import lru_cache

logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class Point:
    x: float
    y: float


@dataclass
class TileInfo:
    path: Path
    x: int
    y: int
    bounds: Tuple[int, int, int, int]


class TileCache:
    def __init__(self, max_size: int = 50):
        self.max_size = max_size
        self._cache: Dict[Tuple[int, int], Image.Image] = {}

    @lru_cache(maxsize=128)
    def _get_tile_key(self, x: int, y: int) -> Tuple[int, int]:
        return (x, y)

    def get(self, x: int, y: int) -> Optional[Image.Image]:
        key = self._get_tile_key(x, y)
        return self._cache.get(key)

    def set(self, x: int, y: int, image: Image.Image) -> None:
        if len(self._cache) >= self.max_size:
            self._cache.pop(next(iter(self._cache)))
        self._cache[(x, y)] = image.copy()


class GTAVTileViewer:
    TILE_SIZE = 256
    SCALE_X = 1.82
    SCALE_Y = -1.82
    CENTER_X = 7535.12
    CENTER_Y = 15291.00

    def __init__(self, tiles_dir: str = "assets"):
        self.tiles_dir = Path(tiles_dir)
        self.tiles: Dict[Tuple[int, int], TileInfo] = {}
        self.tile_cache = TileCache()

        self._load_tiles()
        self._calculate_bounds()

    def _load_tiles(self) -> None:
        for x_dir in self.tiles_dir.iterdir():
            if not x_dir.is_dir():
                continue

            try:
                x = int(x_dir.name)
            except ValueError:
                continue

            for tile_path in x_dir.glob("*.jpg"):
                try:
                    y = int(tile_path.stem)
                    self.tiles[(x, y)] = TileInfo(
                        path=tile_path,
                        x=x,
                        y=y,
                        bounds=(0, 0, self.TILE_SIZE, self.TILE_SIZE)
                    )
                except ValueError:
                    continue

        if not self.tiles:
            raise ValueError("No tiles found in directory")

    def _calculate_bounds(self) -> None:
        xs = [tile.x for tile in self.tiles.values()]
        ys = [tile.y for tile in self.tiles.values()]

        self.min_x = min(xs)
        self.max_x = max(xs)
        self.min_y = min(ys)
        self.max_y = max(ys)

        self.width_tiles = self.max_x - self.min_x + 1
        self.height_tiles = self.max_y - self.min_y + 1

        self.map_width = self.width_tiles * self.TILE_SIZE
        self.map_height = self.height_tiles * self.TILE_SIZE

        logger.info(f"Loaded {len(self.tiles)} tiles, grid: {self.width_tiles}x{self.height_tiles}")

    def world_to_pixel(self, point: Point) -> Point:
        x = int(self.CENTER_X + point.x * self.SCALE_X)
        y = int(self.CENTER_Y + point.y * self.SCALE_Y)
        return Point(
            max(0, min(x, self.map_width - 1)),
            max(0, min(y, self.map_height - 1))
        )

    def _get_tile_at_pixel(self, pixel_x: int, pixel_y: int) -> Optional[TileInfo]:
        tile_x = self.min_x + pixel_x // self.TILE_SIZE
        tile_y = self.min_y + pixel_y // self.TILE_SIZE
        return self.tiles.get((tile_x, tile_y))

    def _load_tile_image(self, tile: TileInfo) -> Optional[Image.Image]:
        cached = self.tile_cache.get(tile.x, tile.y)
        if cached:
            return cached

        try:
            image = Image.open(tile.path)
            self.tile_cache.set(tile.x, tile.y, image)
            return image
        except Exception as e:
            logger.warning(f"Failed to load tile {tile.x},{tile.y}: {e}")
            return None

    def _get_tiles_in_region(self, left: int, top: int, right: int, bottom: int) -> List[TileInfo]:
        tiles = []

        start_x = self.min_x + left // self.TILE_SIZE
        end_x = self.min_x + (right - 1) // self.TILE_SIZE
        start_y = self.min_y + top // self.TILE_SIZE
        end_y = self.min_y + (bottom - 1) // self.TILE_SIZE

        for x in range(start_x, end_x + 1):
            for y in range(start_y, end_y + 1):
                tile = self.tiles.get((x, y))
                if tile:
                    tiles.append(tile)

        return tiles

    def get_fragment(self, world_point: Point, size_x: int = 700, size_y: int = 700, show_dot: bool = True,
                     dot_color: str = "green") -> Image.Image:
        center_pixel = self.world_to_pixel(world_point)

        left = max(0, center_pixel.x - size_x // 2)
        top = max(0, center_pixel.y - size_y // 2)
        right = min(self.map_width, left + size_x)
        bottom = min(self.map_height, top + size_y)

        fragment = Image.new('RGB', (right - left, bottom - top))

        tiles = self._get_tiles_in_region(left, top, right, bottom)

        for tile in tiles:
            tile_image = self._load_tile_image(tile)
            if not tile_image:
                continue

            tile_left = (tile.x - self.min_x) * self.TILE_SIZE
            tile_top = (tile.y - self.min_y) * self.TILE_SIZE

            crop_left = max(left - tile_left, 0)
            crop_top = max(top - tile_top, 0)
            crop_right = min(self.TILE_SIZE, right - tile_left)
            crop_bottom = min(self.TILE_SIZE, bottom - tile_top)

            if crop_right <= crop_left or crop_bottom <= crop_top:
                continue

            cropped = tile_image.crop((crop_left, crop_top, crop_right, crop_bottom))

            paste_x = tile_left + crop_left - left
            paste_y = tile_top + crop_top - top

            fragment.paste(cropped, (int(paste_x), int(paste_y)))

        if fragment.size != (size_x, size_y):
            fragment = fragment.resize((size_x, size_y), Image.Resampling.LANCZOS)
            dot_position = Point(size_x // 2, size_y // 2)
        else:
            dot_position = Point(center_pixel.x - left, center_pixel.y - top)

        if show_dot:
            self._draw_dot(fragment, dot_position, dot_color)

        return fragment

    def _draw_dot(self, image: Image.Image, position: Point, color: str) -> None:
        draw = ImageDraw.Draw(image)

        colors = {
            "red": (255, 0, 0),
            "green": (0, 255, 0),
            "blue": (0, 0, 255)
        }

        dot_color = colors.get(color.lower(), (255, 0, 0))

        dot_size = 2
        draw.ellipse([
            position.x - dot_size,
            position.y - dot_size,
            position.x + dot_size,
            position.y + dot_size
        ], fill=dot_color)


def main() -> None:
    import argparse

    parser = argparse.ArgumentParser(description="GTA V Map Tile Viewer")
    parser.add_argument("tiles_dir", nargs="?", default="assets",
                        help="Directory containing map tiles")
    parser.add_argument("-x", type=float, required=True,
                        help="World X coordinate")
    parser.add_argument("-y", type=float, required=True,
                        help="World Y coordinate")
    parser.add_argument("-sx", "--size_x", type=int, default=700,
                        help="Output image width in pixels")
    parser.add_argument("-sy", "--size_y", type=int, default=700,
                        help="Output image height in pixels")
    parser.add_argument("-o", "--output", default="fragment.jpg",
                        help="Output file name")
    parser.add_argument("-c", "--color", default="green",
                        choices=["red", "green", "blue"],
                        help="Dot color")

    args = parser.parse_args()

    try:
        viewer = GTAVTileViewer(args.tiles_dir)
        world_point = Point(args.x, args.y)

        fragment = viewer.get_fragment(
            world_point=world_point,
            size_x=args.size_x,
            size_y=args.size_y,
            dot_color=args.color
        )

        fragment.save(args.output, quality=100)
        logger.info(f"Saved fragment to {args.output}")

    except Exception as e:
        logger.error(f"Error: {e}")
        raise


if __name__ == "__main__":
    main()