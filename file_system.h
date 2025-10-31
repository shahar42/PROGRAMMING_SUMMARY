#ifndef FILE_SYSTEM_H
#define FILE_SYSTEM_H

#include <iostream>
#include <string>
#include <vector>
#include <list>

#include "utils.h"

class item
{
public:
    virtual ~item() NOEXCEPT;

    virtual std::string getName() const = 0;
    virtual void setName(const std::string& name) = 0;
    virtual void print(std::ostream& os) const = 0;
    virtual size_t GetSize() const = 0;
    virtual item* clone() = 0;

protected:
    item();

private:

};


class Named : public item
{
public:
    Named(const std::string& name);

    std::string getName() const NOEXCEPT;
    void setName(const std::string& newName);
    virtual void print(std::ostream& os) const = 0;
    virtual size_t GetSize() const = 0;
    virtual item* clone() = 0;

protected:
    std::string name;

private:
    // Disable copy+assignment
    Named(const Named&);
    Named& operator=(const Named&);
};


class file : public Named
{
public:
    file(size_t size);

    void print(std::ostream& os) const OVERRIDE;
    size_t GetSize() const NOEXCEPT;
    item* clone() OVERRIDE;

private:
    //disable asssignment + copy
    file& operator=(const file& other);
    file(const file& other);
    std::vector<char> m_content;
    size_t m_size;
};


class directory : public Named
{
public:
    virtual ~directory() OVERRIDE;

    size_t GetSize() const NOEXCEPT OVERRIDE;

    void print(std::ostream& os) const = 0;
    item* clone() = 0;
    virtual void addItem(item* child) = 0;
    virtual void removeItem(const std::string& name) = 0;
    virtual item* findItem(const std::string& name) = 0;

protected:
    std::vector<item*> children;

private:
    // Disable copy +vassignment
    directory(const directory&);
    directory& operator=(const directory&);
};

class RDirectory : public directory
{
public:
    void print(std::ostream& os) const OVERRIDE;
    virtual void addItem(item* child) OVERRIDE;
    virtual void removeItem(const std::string& name) OVERRIDE;
    virtual item* findItem(const std::string& name) OVERRIDE;
    const std::vector<Named*>& GetdList(const std::string name) const;
private:
    RDirectory(const RDirectory&);
    RDirectory& operator=(const RDirectory&);
};

#endif // FILE_SYSTEM_H
