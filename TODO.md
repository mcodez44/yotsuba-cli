# TODO

## Future renderer additions

- Support registration of custom block classes in `chunks2lines()`
- Allow custom blocks to provide their own layout behavior
- Preserve scroll anchoring and block identity for custom block types
- Maintain compatibility with existing block classes

## Minor renderer adjustments

- Unicode-aware width calculation for the renderer
- Safer html parsing -> avoid escaped literal markup being interpreted as actual tags

## Potential new features

- show SFW/NSFW labels in `boards()`
- smart status bar
    - possible examples:
        - /board/ - title
        - /board/ No.123456 - Subject
        - /board/ No.123456 - 8 replies
- visiting threads by their numeric post ID
- page refresh for both index pages & individual threads
- open index or thread in external browser

