# API

- This serves as an API for a mobile application for ticket verification via a QR code and for a web administration
- Below are provided methods with corresponding input and output values
- Api should run in a provided docker container with https and is **_BY NO MEANS SECURE_** as it uses http as communication with outside of it
- All the authentication must be done by other means, this only uses forwarded basic-auth packets for user-table assignment
- Use of https for communication with the server on the internet is highly recommended (maybe even mandatory)
- This api is definitely not 100% bug-free
- Requirements for python must be met and only Python3 is (and will be) supported
- Api requires all the provided folders to be present in order to function properly
- Do not expose this api (or folder with the code) directly to the outside

## Browser route: /api/ui/\* :

---

### **create_table** _(201, 304, 400, 500, 406)_

- creates a new table for ticket codes

```json
input format:

{
  "table_name": "",
  "size": ""
}
```

---

### **delete_table** _(200, 304)_

- deletes a table containing ticket codes

```json
input format:

{
  "table_name": ""
}
```

---

### **backup_db** _(200, 500)_

- backs up databases with codes and assigned users into a zip file

```json
input format:

{}
```

---

### **restore_db** _(200, 304)_

- restores databases from a zip backup

```json
input format:

{
  "filepath": ""
}
```

---

### **clear_table** _(200, 304)_

- clears a given table of codes

```json
input format:

{
  "table_name": ""
}

```

---

### **add_entries** _(201, 304, 400, 500)_

- adds _n_ codes into a table
- codes are generated based on the internal parameters

```json
input format:

{
  "table_name": "",
  "code": ""
}
```

---

### **select_code** _(200 + json, 400)_

- returns a row with matching code from a table

```json
input format:

{
  "table_name": "",
  "code": ""
}
```

```json
output format:

{
    "id": "",
    "code": "",
    "used": "",
    "time": ""
}
```

---

### **update_code** _(200 + json, 304, 400)_

- updates a code to current time and increments used count
- returns values pre-update

```json
input format:

{
    "table_name": "",
    "code": ""
}
```

```json
output format:

{
    "id": "",
    "code": "",
    "used": "",
    "time": ""
}
```

---

### **add_users** _(200, 304, 400)_

- adds users from a list into the assingment table and assigns them to table_name

```json
input format:

{
    "table_name": "",
    "users": ""
}
```

---

### **delete_all_users** _(200, 304)_

- deletes all users from assignment table

```json
input format:

{}
```

---

### **delete_users_for_table** _(200, 304)_

- deletes all users from assginment table assigned to a specific table

```json
input format:

{
    "table_name": ""
}
```

---

### **assigned_user_table** _(200 + json, 400)_

- returns name of a table the specified user is assigned to

```json
input format:

{
    "user": ""
}
```

```json
output format:

{
    "table_name": ""
}
```

---

### **export_tickets** _(200 + json, 400)_

- exports tickets from a table to a file and provides the download link for it
- currently only supports HTML (printing to pdf on client side browser) and one template with 8 codes
- TODO: accidentally removed after fedora update completely ruined itself and grub :( (forgot to push) -> restore previous state where printing was to a pdf instead of html

```json
input format:

{
    "table_name": ""
}
```

```json
output format:

{
    "id": "",
    "code": "",
    "used": "",
    "time": ""
}
```

---

**_WORK IN PROGRESS_**
