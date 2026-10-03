# Ubai Wilson — Landing Page

A single, self-contained `index.html` link-in-bio page (IQI Realty, Johor Bahru).

## Editing
Everything editable (WhatsApp number, messages, email, social links, images, projects)
lives in the `CONFIG` block at the top of the `<script>` near the end of `index.html`.

- **Hide something:** set it to `""` (e.g. `email`, Instagram `url`).
- **Unknown project details:** keep `"On request"`.
- **Add a project:** copy one `{ ... }` block inside `projects`, paste it after the last one
  (with a comma between blocks) and edit the values.
- **Photo framing:** `imagePosition` (e.g. `"center 30%"`) picks what stays in view;
  `imageFit: "contain"` shows a tall/portrait photo uncropped over a soft blurred backdrop.
  `imageAspect: "4 / 5"` gives a tall photo a portrait frame on phones (default `"4 / 3"`).

## Adding photos
Images are embedded as base64 JPGs (~1000px wide) so the page is one file:

```bash
pip install pillow
python3 tools/embed_images.py --portrait me.jpg --logo iqi-logo.png
python3 tools/embed_images.py --hero jb-skyline.jpg
python3 tools/embed_images.py --namecard card.jpg
python3 tools/embed_images.py --project "EXSIM Kebun Teh=exsim.jpg"
```

The portrait is cropped to 4:5 (keeping the face area), logos with transparency are
flattened onto white, cut-out (transparent) portraits are placed on the page's Old Lace base colour,
and phone rotation is corrected automatically. The name card appears in the contact section
next to a "Save Contact" button (a vCard built from CONFIG).

## SEO / sharing
Title, description and Open Graph tags are in `<head>`. After hosting, fill in the
commented `canonical`, `og:url` and `og:image` (social apps need a public image URL).
