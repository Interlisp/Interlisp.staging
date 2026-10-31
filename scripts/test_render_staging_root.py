#!/usr/bin/env python3
import pathlib
import tempfile
import unittest

import render_staging_root as render


class RenderStagingRootTest(unittest.TestCase):
    def setUp(self):
        self.templates = (
            pathlib.Path(__file__).resolve().parent.parent / ".github" / "pages"
        )

    def render(self, previews):
        with tempfile.TemporaryDirectory() as tmp:
            tmp = pathlib.Path(tmp)
            previews_file = tmp / "previews.txt"
            previews_file.write_text(
                "\n".join(str(number) for number in previews) + "\n",
                encoding="utf-8",
            )
            output = tmp / "out"
            render.main([
                "--templates-dir", str(self.templates),
                "--previews-file", str(previews_file),
                "--output", str(output),
            ])
            return {
                path.name: path.read_text(encoding="utf-8")
                for path in output.iterdir()
            }

    def test_renders_sorted_previews(self):
        files = self.render([355, 357, 355])
        self.assertIn('href="pr-357/"', files["index.html"])
        self.assertIn('href="pr-355/"', files["index.html"])
        self.assertLess(
            files["index.html"].index("pr-357/"),
            files["index.html"].index("pr-355/"),
        )
        self.assertNotIn("<!-- PREVIEWS -->", files["index.html"])
        self.assertNotIn("{{BASE_PATH}}", files["index.html"])
        self.assertIn('href="pr-357/"', files["404.html"])
        self.assertEqual(files["robots.txt"], "User-agent: *\nDisallow: /\n")
        self.assertEqual(files[".nojekyll"], "")

    def test_empty_previews(self):
        files = self.render([])
        self.assertIn("No previews are currently deployed.", files["index.html"])

    def test_rejects_invalid_preview(self):
        with self.assertRaises(ValueError):
            render.parse_preview_lines(["abc"])

    def test_rejects_missing_template(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp = pathlib.Path(tmp)
            previews_file = tmp / "previews.txt"
            previews_file.write_text("357\n", encoding="utf-8")
            with self.assertRaises(FileNotFoundError):
                render.main([
                    "--templates-dir", str(tmp / "missing"),
                    "--previews-file", str(previews_file),
                    "--output", str(tmp / "out"),
                ])


if __name__ == "__main__":
    unittest.main()
