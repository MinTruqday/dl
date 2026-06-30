import re

def swap_aside_main(filepath):
    with open(filepath, 'r') as f:
        content = f.read()

    # Find aside and main using regex
    # We will just change the class names to use order!
    # aside className="lg:col-span-X ... -> aside className="lg:col-span-X order-2 lg:order-2 ...
    # main className="lg:col-span-Y ... -> main className="lg:col-span-Y order-1 lg:order-1 ...
    # This is much safer than parsing HTML tags.

    content = re.sub(r'(<aside className=")(lg:col-span-\d+)', r'\1\2 order-first lg:order-last', content)
    
    with open(filepath, 'w') as f:
        f.write(content)

swap_aside_main("frontend/app/(main)/cong-tac/page.tsx")
swap_aside_main("frontend/app/(main)/tai-lieu/page.tsx")

