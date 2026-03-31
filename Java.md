---
id: Java
aliases: []
tags: []
---

---
>[!NOTE] Comes from (NORTH):

[[Programming Languages - High-level languages]]
[[Programming Languages - Statically Typed]]
 
>[!NOTE] Will lead (SOUTH) to:

>[!NOTE] Is Similar (WEST) to:

>[!NOTE] Is Opposite (EAST) to:

---
>[!INFO] Additional links about Java

Tags: 
Source: 
* [Books to learn JAVA](https://blogs.oracle.com/javamagazine/post/latest-java-books)
  * OCP exercises [github](https://github.com/egch/1Z0-829-preparation)
* [JavaPoint](https://www.javatpoint.com/)  
---

# Java

It is a general-purpose programming language intended to let application developers write once, run anywhere (WORA),
meaning that compiled Java code can run on all platforms that support Java without the need for recompilation. Java
applications are typically compiled to bytecode that can run on any Java virtual machine (JVM) regardless of the
underlying computer architecture. Java is widely used in various domains of software development, including:

1. **Web Development**: Java is used to build web applications and services. Technologies like Servlets, JavaServer
   Pages (JSP), and JavaServer Faces (JSF) are used to create dynamic web content. Frameworks like Spring and Struts
   are popular for building enterprise-level web applications.
2. **Enterprise Applications**: Java is a popular choice for building large-scale enterprise applications due to its
   robustness, scalability, and security features. Java EE (Enterprise Edition) provides a set of specifications for
   developing and deploying large-scale, multi-tiered, scalable, reliable, and secure network applications.
3. **Mobile Applications**: Java is used to develop Android applications. The Android operating system uses the
   Java programming language, and the Android Software Development Kit (SDK) provides libraries and tools needed to
   build apps for Android devices.
4. **Desktop Applications**: Java is used to create desktop applications that run on Windows, macOS, and Linux.
   JavaFX is a software platform for creating and delivering desktop applications, as well as rich internet
   applications (RIAs) that can run across a wide variety of devices.
5. **Games Development**: Java is also used in game development, especially for creating browser-based games or
   games that run on the Java platform. Libraries like LibGDX and JMonkeyEngine are used for game development in
   Java.
6. **Big Data and Analytics**: Java is used in big data technologies like Hadoop and Apache Spark for processing
   large datasets. It's also used in data analytics and machine learning applications.
7. **Internet of Things (IoT)**: Java is used in IoT applications due to its platform independence and robustness.
   It's used in smart home devices, industrial automation, and wearable technology.
 
Java's versatility, strong community support, and extensive libraries and frameworks make it a popular choice for
developers across various domains

## Java History

![Java History](assets/img/Java%20History.png)

## Use of Java

![Java Use Cases](assets/img/Java%20Use%20Cases.png)

## Java vs C++
![java vs c++](assets/img/Java%20vs%20c++.png)

more info abou it:
- [20 Key Differences between C++ and Java](https://www.mygreatlearning.com/blog/cpp-vs-java/)

## Java Features

The Java tutorial outlined above is a comprehensive and structured learning path designed for beginners as well as 
experienced developers. It covers every essential topic in Java, starting from foundational concepts like syntax, 
variables, and control statements, progressing through object-oriented principles such as inheritance, polymorphism, 
and encapsulation, and extending into advanced areas like multithreading, I/O handling, collections, networking, JDBC, 
and Java 8 features. Special focus is given to key Java features—such as platform independence, security, robustness, 
and simplicity—that have made Java one of the most popular and enduring programming languages. Additionally, the 
tutorial includes a wide range of code examples, practice programs, and real-world Java projects (many built with JSP 
and servlets), making it a valuable resource for mastering Java from the ground up and applying it in practical applications.

## JVM, JRE and JDK

### JRE

![JRE image](assets/img/JRE.png)
![JRE process image](assets/img/JRE%20process.png)

### JDK

![jdk img](assets/img/JDK.png)
![JDK process](assets/img/JDK%20process.png)

### JVM, JDK, JRE - Deep Drive

![JDK, JRE, JV](assets/img/JDK,%20JRE,%20JVM.png)

#### How do JVM, JRE, and JDK work together to enable Java code execution?

JDK compiles the code, JRE provides the runtime environment, JVM executes the bytecode

## How Java code is executed? 

![Java Execution img](assets/img/Java%20Execution.png)

## Run Java

```bash
javac HelloWorld.java
# you'll get a HelloWorld.class file
java HelloWorld

# you can also run java on the prompt with jshell
jshell # Ctrl + D to exit
```

#### Install JAVA on Arch Linux

```bash
yay -S jdk-openjdk openjdk-doc openjdk-src
```

### Install Java on debian

```bash
sudo apt install openjdk-21-jdk openjdk-21-doc
```
