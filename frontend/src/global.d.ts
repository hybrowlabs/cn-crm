declare namespace crm {
    interface Widget {
        render: (el: HTMLElement) => void
    }
    let am_dashboard_widget: Widget | undefined;
    let combined_dashboard_widget: Widget | undefined;
    let pending_tasks_widget: Widget | undefined;
}

declare global {
    interface Window {
        crm: typeof crm
    }
    let crm: typeof crm
}

export { }

declare module 'frappe-ui' {
    import { Component } from 'vue'
    export const Breadcrumbs: Component
    export const Button: Component
    export const Input: Component
    export const FormControl: Component
    export const Dropdown: Component
    export const Modal: Component
    export const LoadingIndicator: Component
    export const Badge: Component
    export const Avatar: Component
    export const Checkbox: Component
    export const DatePicker: Component
    export const Switch: Component
    export const Tooltip: Component
    export const Popover: Component
    export const Toast: Component
    export const Dialog: Component
    export const Tab: Component
    export const Tabs: Component
    export const ListItem: Component
    export const ListView: Component
    export const ErrorMessage: Component
    export const Card: Component
    export const TextEditor: Component
    export const FileUploader: Component
}

