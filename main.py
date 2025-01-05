from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.popup import Popup
from kivy.uix.spinner import Spinner
from kivy.uix.gridlayout import GridLayout
from kivy.uix.scrollview import ScrollView
from kivy.uix.boxlayout import BoxLayout
from kivy.app import App
import psycopg2
import pandas as pd

conn = psycopg2.connect(
    dbname="ecommerce",
    user="postgres",
    password="admin",
    host="localhost",
    port="5433"
)
cursor = conn.cursor()

class NumericInput(TextInput):
    def insert_text(self, substring, from_undo=False):
        if substring.isdigit() or substring == '.':
            return super().insert_text(substring, from_undo=from_undo)
        return ''

class EcommerceApp(App):
    def build(self):
        self.layout = BoxLayout(orientation='vertical', padding=10, spacing=10)

        self.layout.add_widget(Label(text='Manajemen Produk', size_hint_y=None, height=40, font_size=20, bold=True))
        self.product_name = TextInput(hint_text='Nama Produk', size_hint_y=None, height=40)
        self.product_description = TextInput(hint_text='Deskripsi', size_hint_y=None, height=40)
        self.product_price = NumericInput(hint_text='Harga', size_hint_y=None, height=40)
        self.product_stock = NumericInput(hint_text='Stok', size_hint_y=None, height=40)
        self.layout.add_widget(self.product_name)
        self.layout.add_widget(self.product_description)
        self.layout.add_widget(self.product_price)
        self.layout.add_widget(self.product_stock)

        self.add_product_btn = Button(text='Tambah Produk', size_hint_y=None, height=40, background_color=(0, 0.7, 0, 1))
        self.add_product_btn.bind(on_press=self.tambah_produk)
        self.layout.add_widget(self.add_product_btn)

        self.layout.add_widget(Label(text='Manajemen Pesanan', size_hint_y=None, height=40, font_size=20, bold=True))
        self.customer_name = TextInput(hint_text='Nama Pelanggan', size_hint_y=None, height=40)
        self.customer_email = TextInput(hint_text='Email Pelanggan', size_hint_y=None, height=40)
        self.layout.add_widget(self.customer_name)
        self.layout.add_widget(self.customer_email)

        self.product_spinner = Spinner(text='Pilih Produk', size_hint_y=None, height=40)
        self.update_product_spinner()
        self.layout.add_widget(self.product_spinner)

        self.quantity = NumericInput(hint_text='Jumlah', size_hint_y=None, height=40)
        self.layout.add_widget(self.quantity)

        self.add_order_btn = Button(text='Tambah Pesanan', size_hint_y=None, height=40, background_color=(0, 0.7, 0, 1))
        self.add_order_btn.bind(on_press=self.tambah_pesanan)
        self.layout.add_widget(self.add_order_btn)

        self.export_btn = Button(text='Ekspor ke Excel', size_hint_y=None, height=40, background_color=(0.2, 0.6, 1, 1))
        self.export_btn.bind(on_press=self.ekspor_ke_excel)
        self.layout.add_widget(self.export_btn)

        self.list_products_btn = Button(text='Daftar Produk', size_hint_y=None, height=40, background_color=(0.2, 0.6, 1, 1))
        self.list_products_btn.bind(on_press=self.tampilkan_popup_produk)
        self.layout.add_widget(self.list_products_btn)

        self.list_orders_btn = Button(text='Daftar Pesanan', size_hint_y=None, height=40, background_color=(0.2, 0.6, 1, 1))
        self.list_orders_btn.bind(on_press=self.tampilkan_popup_pesanan)
        self.layout.add_widget(self.list_orders_btn)

        return self.layout

    def update_product_spinner(self):
        cursor.execute("SELECT name FROM products")
        products = cursor.fetchall()
        self.product_spinner.values = [product[0] for product in products]

    def tambah_produk(self, instance):
        nama = self.product_name.text
        deskripsi = self.product_description.text
        harga = self.product_price.text
        stok = self.product_stock.text

        if not harga.replace('.', '', 1).isdigit() or not stok.isdigit():
            self.tampilkan_popup('Error', 'Harga dan Stok harus berupa angka.')
            return

        harga = float(harga)
        stok = int(stok)

        cursor.execute("INSERT INTO products (name, description, price, stock) VALUES (%s, %s, %s, %s)",
                       (nama, deskripsi, harga, stok))
        conn.commit()
        self.update_product_spinner()
        self.tampilkan_popup('Produk Ditambahkan', f'Produk {nama} berhasil ditambahkan.')

    def tambah_pesanan(self, instance):
        nama_pelanggan = self.customer_name.text
        email_pelanggan = self.customer_email.text
        produk_terpilih = self.product_spinner.text
        jumlah = self.quantity.text

        if not jumlah.isdigit():
            self.tampilkan_popup('Error', 'Jumlah harus berupa angka.')
            return

        jumlah = int(jumlah)

        cursor.execute("SELECT product_id, price, stock FROM products WHERE name = %s", (produk_terpilih,))
        produk = cursor.fetchone()
        if produk is None:
            self.tampilkan_popup('Error', 'Produk tidak ditemukan.')
            return

        product_id, harga_per_unit, stok = produk

        if stok < jumlah:
            self.tampilkan_popup('Error', 'Stok tidak mencukupi.')
            return

        total_harga = jumlah * harga_per_unit

        cursor.execute("INSERT INTO orders (customer_name, customer_email, total_amount) VALUES (%s, %s, %s) RETURNING order_id",
                    (nama_pelanggan, email_pelanggan, total_harga))
        order_id = cursor.fetchone()[0]

        cursor.execute("INSERT INTO order_items (order_id, product_id, quantity, price_per_unit) VALUES (%s, %s, %s, %s)",
                    (order_id, product_id, jumlah, harga_per_unit))

        stok_baru = stok - jumlah
        cursor.execute("UPDATE products SET stock = %s WHERE product_id = %s", (stok_baru, product_id))

        conn.commit()
        self.tampilkan_popup('Pesanan Ditambahkan', f'Pesanan untuk {nama_pelanggan} berhasil ditambahkan.')
        self.update_product_spinner()

    def ekspor_ke_excel(self, instance):
        try:
            products_df = pd.read_sql_query("SELECT * FROM products", conn)
            products_df.to_excel('produk.xlsx', index=False, sheet_name='Produk')

            orders_df = pd.read_sql_query("SELECT * FROM orders", conn)
            order_items_df = pd.read_sql_query("SELECT * FROM order_items", conn)
            
            order_details_df = pd.merge(order_items_df, products_df, on='product_id', how='left')
            order_details_df = pd.merge(order_details_df, orders_df, on='order_id', how='left')
            
            order_list_df = order_details_df[['order_id', 'customer_name', 'customer_email', 'name', 'quantity', 'price_per_unit', 'total_amount', 'order_date']]
            order_list_df.rename(columns={
                'name': 'product_name',
                'quantity': 'product_quantity',
                'price_per_unit': 'product_price_per_unit'
            }, inplace=True)
            
            order_list_df.to_excel('daftar_pesanan.xlsx', index=False, sheet_name='Daftar Pesanan')

            self.tampilkan_popup('Ekspor Berhasil', 'Data berhasil diekspor ke dua file Excel: produk.xlsx dan daftar_pesanan.xlsx.')
        
        except Exception as e:
            self.tampilkan_popup('Error', f'Terjadi kesalahan saat mengekspor data: {str(e)}')

    def tampilkan_popup(self, judul, pesan):
        popup_layout = BoxLayout(orientation='vertical', padding=10, spacing=10)
        popup_layout.add_widget(Label(text=pesan, size_hint_y=None, height=40))
        close_btn = Button(text='Tutup', size_hint_y=None, height=40, background_color=(0.8, 0.2, 0.2, 1))
        popup_layout.add_widget(close_btn)
        popup = Popup(title=judul, content=popup_layout, size_hint=(0.8, 0.4))
        close_btn.bind(on_press=popup.dismiss)
        popup.open()

    def tampilkan_popup_produk(self, instance):        
        cursor.execute("SELECT * FROM products")
        produk = cursor.fetchall()

        scroll_layout = GridLayout(cols=5, spacing=10, size_hint_y=None, padding=10)
        scroll_layout.bind(minimum_height=scroll_layout.setter('height'))

        scroll_layout.add_widget(Label(text='Nama', size_hint_y=None, height=40, bold=True))
        scroll_layout.add_widget(Label(text='Deskripsi', size_hint_y=None, height=40, bold=True))
        scroll_layout.add_widget(Label(text='Harga', size_hint_y=None, height=40, bold=True))
        scroll_layout.add_widget(Label(text='Stok', size_hint_y=None, height=40, bold=True))
        scroll_layout.add_widget(Label(text='Aksi', size_hint_y=None, height=40, bold=True))

        for p in produk:
            scroll_layout.add_widget(Label(text=p[1], size_hint_y=None, height=40))
            scroll_layout.add_widget(Label(text=p[2], size_hint_y=None, height=40))
            scroll_layout.add_widget(Label(text=f"Rp. {p[3]:.2f}", size_hint_y=None, height=40))
            scroll_layout.add_widget(Label(text=str(p[4]), size_hint_y=None, height=40))

            action_layout = BoxLayout(orientation='horizontal', size_hint_y=None, height=40, spacing=5)
            update_btn = Button(text='Perbarui', size_hint_x=None, width=80, background_color=(0.2, 0.6, 1, 1))
            delete_btn = Button(text='Hapus', size_hint_x=None, width=80, background_color=(0.8, 0.2, 0.2, 1))
            update_btn.bind(on_press=lambda btn, p=p: self.perbarui_produk(p))
            delete_btn.bind(on_press=lambda btn, p=p: self.hapus_produk(p))
            action_layout.add_widget(update_btn)
            action_layout.add_widget(delete_btn)
            scroll_layout.add_widget(action_layout)

        scroll_view = ScrollView(size_hint=(1, None), size=(800, 400))
        scroll_view.add_widget(scroll_layout)

        popup_layout = BoxLayout(orientation='vertical', padding=10, spacing=10)
        popup_layout.add_widget(scroll_view)
        close_btn = Button(text='Tutup', size_hint_y=None, height=40, background_color=(0.8, 0.2, 0.2, 1))
        close_btn.bind(on_press=lambda instance: popup.dismiss())
        popup_layout.add_widget(close_btn)

        popup = Popup(title='Daftar Produk', content=popup_layout, size_hint=(0.9, 0.8))
        popup.open()

    def tampilkan_popup_pesanan(self, instance):
        cursor.execute("SELECT * FROM orders")
        pesanan = cursor.fetchall()

        scroll_layout = GridLayout(cols=1, spacing=10, size_hint_y=None)
        scroll_layout.bind(minimum_height=scroll_layout.setter('height'))

        header_layout = BoxLayout(orientation='horizontal', size_hint_y=None, height=40)
        header_layout.add_widget(Label(text='Nama Pelanggan', size_hint_x=0.3, bold=True))
        header_layout.add_widget(Label(text='Email Pelanggan', size_hint_x=0.3, bold=True))
        header_layout.add_widget(Label(text='Total Harga', size_hint_x=0.2, bold=True))
        header_layout.add_widget(Label(text='Tanggal Pesanan', size_hint_x=0.2, bold=True))
        header_layout.add_widget(Label(text='Aksi', size_hint_x=0.1, bold=True))
        scroll_layout.add_widget(header_layout)

        for pesan in pesanan:
            order_layout = BoxLayout(orientation='horizontal', size_hint_y=None, height=40)
            order_layout.add_widget(Label(text=pesan[1], size_hint_x=0.3))
            order_layout.add_widget(Label(text=pesan[2], size_hint_x=0.3))
            order_layout.add_widget(Label(text=f"Rp. {pesan[3]:.2f}", size_hint_x=0.2))
            order_layout.add_widget(Label(text=pesan[4].strftime('%Y-%m-%d %H:%M'), size_hint_x=0.2))
            delete_btn = Button(text='Hapus', size_hint_x=0.1, background_color=(0.8, 0.2, 0.2, 1))
            delete_btn.bind(on_press=lambda btn, o=pesan: self.hapus_pesanan(o))
            order_layout.add_widget(delete_btn)
            scroll_layout.add_widget(order_layout)

        scroll_view = ScrollView(size_hint=(1, None), size=(800, 400))
        scroll_view.add_widget(scroll_layout)

        popup_layout = BoxLayout(orientation='vertical', padding=10, spacing=10)
        popup_layout.add_widget(scroll_view)
        close_btn = Button(text='Tutup', size_hint_y=None, height=40, background_color=(0.8, 0.2, 0.2, 1))
        close_btn.bind(on_press=lambda instance: popup.dismiss())
        popup_layout.add_widget(close_btn)

        popup = Popup(title='Daftar Pesanan', content=popup_layout, size_hint=(0.9, 0.8))
        popup.open()

    def perbarui_produk(self, produk):
        update_popup_layout = BoxLayout(orientation='vertical', padding=10, spacing=10)
        update_popup_layout.add_widget(Label(text=f"Perbarui Produk: {produk[1]}", size_hint_y=None, height=40))

        new_name = TextInput(text=produk[1], hint_text='Nama Baru', size_hint_y=None, height=40)
        new_description = TextInput(text=produk[2], hint_text='Deskripsi Baru', size_hint_y=None, height=40)
        new_price = NumericInput(text=str(produk[3]), hint_text='Harga Baru', size_hint_y=None, height=40)
        new_stock = NumericInput(text=str(produk[4]), hint_text='Stok Baru', size_hint_y=None, height=40)

        update_popup_layout.add_widget(new_name)
        update_popup_layout.add_widget(new_description)
        update_popup_layout.add_widget(new_price)
        update_popup_layout.add_widget(new_stock)

        save_btn = Button(text='Simpan', size_hint_y=None, height=40, background_color=(0, 0.7, 0, 1))
        save_btn.bind(on_press=lambda btn: self.simpan_perbaruan_produk(produk[0], new_name.text, new_description.text, new_price.text, new_stock.text))
        update_popup_layout.add_widget(save_btn)

        update_popup = Popup(title='Perbarui Produk', content=update_popup_layout, size_hint=(0.8, 0.8))
        update_popup.open()

    def simpan_perbaruan_produk(self, product_id, new_name, new_description, new_price, new_stock):
        if not new_price.replace('.', '', 1).isdigit() or not new_stock.isdigit():
            self.tampilkan_popup('Error', 'Harga dan Stok harus berupa angka.')
            return

        new_price = float(new_price)
        new_stock = int(new_stock)

        cursor.execute("UPDATE products SET name = %s, description = %s, price = %s, stock = %s WHERE product_id = %s",
                       (new_name, new_description, new_price, new_stock, product_id))
        conn.commit()
        self.tampilkan_popup('Produk Diperbarui', 'Produk berhasil diperbarui.')
        self.update_product_spinner()

    def hapus_produk(self, produk):
        cursor.execute("DELETE FROM order_items WHERE product_id = %s", (produk[0],))
        cursor.execute("DELETE FROM products WHERE product_id = %s", (produk[0],))
        conn.commit()
        self.tampilkan_popup('Produk Dihapus', 'Produk berhasil dihapus.')
        self.update_product_spinner()

    def hapus_pesanan(self, pesanan):
        cursor.execute("DELETE FROM order_items WHERE order_id = %s", (pesanan[0],))
        cursor.execute("DELETE FROM orders WHERE order_id = %s", (pesanan[0],))
        conn.commit()
        self.tampilkan_popup('Pesanan Dihapus', 'Pesanan berhasil dihapus.')

if __name__ == '__main__':
    EcommerceApp().run()