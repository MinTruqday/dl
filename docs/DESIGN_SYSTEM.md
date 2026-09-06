# Veriq Design System

## Direction

Veriq is a quiet editorial workspace

The interface should feel like a well made reading room combined with a precise writing tool

The product uses warm paper surfaces clear typography restrained color and direct language

Veriq does not imitate a generic dashboard

## Principles

- Content comes before chrome
- Text labels come before icons
- One interaction pattern has one visual treatment
- Every action has a visible loading success empty and error state
- Dense work areas remain calm through alignment spacing and hierarchy
- Decoration never competes with documents
- Mobile behavior is designed rather than compressed
- Dark mode is not part of the product

## Color

| Token | Value | Use |
| --- | --- | --- |
| Canvas | `#F7F6F2` | App background |
| Surface | `#FFFFFF` | Main panels |
| Surface quiet | `#F0EFEA` | Selected rows and secondary panels |
| Ink | `#20201E` | Primary text |
| Ink muted | `#6D6C67` | Supporting text |
| Border | `#DDDCD6` | Dividers and controls |
| Brand | `#2F5D50` | Primary action and focus |
| Brand hover | `#244A40` | Primary action hover |
| Danger | `#A33B32` | Destructive action |
| Warning | `#8B651A` | Warning state |

Color is never the only status signal

## Typography

- Interface text uses Inter
- Editorial display text may use Georgia
- Body text is 15px with 1.55 line height
- Page titles are 30px on desktop and 25px on mobile
- Section titles are 18px
- Control labels are 14px
- Metadata is 12px
- Uppercase is reserved for short structural labels

## Spacing

The base unit is 4px

Common gaps are 8px 12px 16px 24px 32px and 48px

Page width is capped at 1280px

Reading width is capped at 760px

## Shape

- Inputs and buttons use 9px radius
- Cards and menus use 12px radius
- Large workspace panels use 16px radius
- Pills are reserved for tags filters and status
- Shadows appear only on floating menus dialogs and dragged objects

## Navigation

Desktop uses a text sidebar

The sidebar shows only routes available to the current role

The top bar contains global search notifications and account controls

Mobile uses a compact top bar and a labeled bottom navigation with no more than five destinations

## Icons

Icons are allowed only when space cannot hold a clear label or when the symbol has a universal interaction meaning

Decorative icons are forbidden

Icon only buttons require an accessible label and tooltip

Lists cards headings metrics and empty states do not receive decorative icons

## Buttons

- Primary for the single main action in a region
- Secondary for normal actions
- Quiet for low emphasis actions
- Danger for confirmed destructive actions
- Icon only for close reveal search and compact editor controls

Button labels describe the result

## Forms

Labels remain visible above fields

Placeholder text never replaces a label

Validation appears next to the affected field

Password reveal is a compact text action

Submit buttons keep their width while loading

## Modals

Every modal uses the shared Modal component

Dialogs use one header one content region and one footer

Escape closes non destructive dialogs

Clicking the backdrop closes non destructive dialogs

Destructive actions require explicit confirmation

## Tables and lists

Tables are used only for comparable fields

Collections use rows when scanning matters and cards when visual content matters

Row actions appear as text in a compact menu

Empty states explain what is missing and offer one useful next action

## Feedback

Loading uses skeletons for content and a small progress indicator for actions

Toasts contain text and a quiet status edge without decorative icons

Success messages state the completed result

Errors state what failed and what the user can do next

## Motion

Interaction transitions use 140ms to 180ms

Large entrance animations and automatic carousels are forbidden

Reduced motion preferences are respected

## Route structure

Route files coordinate data and composition

Reusable interface belongs in `shared/components`

Feature specific interface belongs in `features/<feature>/components`

Network access belongs in `features/<feature>/services`

Shared types belong in `features/<feature>/types`

Pages should not contain duplicated API clients modal implementations or design tokens

## Review checklist

- Uses design tokens rather than new literal colors
- Uses a shared primitive for buttons inputs modals and states
- Contains no decorative icon
- Works at 360px 768px 1024px and 1440px
- Supports keyboard navigation and visible focus
- Includes loading empty error and success behavior where relevant
- Uses direct natural Vietnamese
- Connects to an existing backend contract or states the missing contract
- Contains no comments emoji or textual ellipsis
