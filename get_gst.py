import frappe

def main():
    frappe.init(site='precious-alloys.localhost')
    frappe.connect()
    try:
        f = frappe.get_meta('Customer').get_field('gst_category')
        print('Customer field options:', f.options if f else 'None')
    except Exception as e:
        print('Error Customer meta:', e)
        
    try:
        f = frappe.get_meta('crm_deal').get_field('gst_category')
        print('crm_deal field options:', f.options if f else 'None')
    except Exception as e:
        print('Error crm_deal meta:', e)

if __name__ == "__main__":
    main()
