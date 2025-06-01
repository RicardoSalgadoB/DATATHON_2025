import 'dart:convert';
import 'package:http/http.dart' as http;
import 'package:dash_chat_2/dash_chat_2.dart';
import 'package:flutter/material.dart';

class ChatPage extends StatefulWidget {
  const ChatPage({super.key});
  @override
  State<ChatPage> createState() => _ChatPageState();
}

class _ChatPageState extends State<ChatPage> {
  final ChatUser _currentUser = ChatUser(id: '1', firstName: 'Max', lastName: 'López');
  final ChatUser _gptChatUser = ChatUser(id: '2', firstName: 'Hey', lastName: 'Chat');
  final List<ChatMessage> _messages = <ChatMessage>[];

  // Multiple URL options - try in order
  final List<String> _serverUrls = [
    'http://10.0.2.2:5000/chat/user/18e076d2bedd0c317d8c602959f19778bd80dad3',      // Android Emulator
    'http://192.168.1.100:5000/chat/user/18e076d2bedd0c317d8c602959f19778bd80dad3', // Replace with your actual IP
    'http://127.0.0.1:5000/chat/user/18e076d2bedd0c317d8c602959f19778bd80dad3',     // Localhost fallback
  ];

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        backgroundColor: const Color(0xFF090E22),
        title: const Text(
          'HeyChat',
          style: TextStyle(
            color: Colors.white,
          ),
        ),
      ),
      body: Container(
        color: Colors.black,
        child: DashChat(
          currentUser: _currentUser,
          messageOptions: const MessageOptions(
            currentUserContainerColor: Color(0xFF303030),
            containerColor: Color(0xFF090E22),
            currentUserTextColor: Colors.white,
            textColor: Colors.white,
          ),
          onSend: (ChatMessage m) {
            getChatResponse(m);
          },
          messages: _messages,
          inputOptions: InputOptions(
            inputToolbarPadding: const EdgeInsets.all(8),
            inputDecoration: const InputDecoration(
              filled: true,
              fillColor: Color(0xFF303030),
              border: InputBorder.none,
            ),
            inputTextStyle: const TextStyle(
              color: Colors.white,
              fontSize: 16,
            ),
            sendButtonBuilder: (onSend) => IconButton(
              icon: const Icon(Icons.send, color: Colors.white),
              onPressed: onSend,
            ),
          ),
        ),
      ),
    );
  }

  Future<void> getChatResponse(ChatMessage m) async {
    setState(() {
      _messages.insert(0, m);
    });

    // Try each URL until one works
    for (String urlString in _serverUrls) {
      final url = Uri.parse(urlString);
      
      try {
        final response = await http.post(
          url,
          headers: {
            'Content-Type': 'application/json',
            'Accept': 'application/json',
          },
          body: jsonEncode({'content': m.text}),
        ).timeout(const Duration(seconds: 10)); // Add timeout

        if (response.statusCode == 200) {
          // Try to parse JSON response first
          String responseText;
          try {
            final jsonResponse = jsonDecode(response.body);
            responseText = jsonResponse['message'] ?? jsonResponse['response'] ?? response.body;
          } catch (e) {
            // If not JSON, use raw response
            responseText = response.body;
          }

          // Format the response text for better display
          responseText = _formatResponseText(responseText);

          final botMessage = ChatMessage(
            user: _gptChatUser,
            createdAt: DateTime.now(),
            text: responseText,
          );
          
          setState(() {
            _messages.insert(0, botMessage);
          });
          return; // Success, exit the loop
        } else {
          print('Server responded with status: ${response.statusCode}');
          continue; // Try next URL
        }
      } catch (e) {
        print('Failed to connect to $urlString: $e');
        continue; // Try next URL
      }
    }

    // If all URLs failed
    setState(() {
      _messages.insert(0, ChatMessage(
        user: _gptChatUser,
        createdAt: DateTime.now(),
        text: 'Lo siento, no pude conectar con el servidor. Verifica que el servidor esté ejecutándose.',
      ));
    });
  }

  String _formatResponseText(String text) {
    // Remove excessive asterisks and format text nicely
    String formatted = text;
    
    // Replace **bold** formatting
    formatted = formatted.replaceAllMapped(
      RegExp(r'\*\*(.*?)\*\*'),
      (match) => '${match.group(1)?.toUpperCase()}',
    );
    
    // Replace *italic* formatting with proper emphasis
    formatted = formatted.replaceAllMapped(
      RegExp(r'\*(.*?)\*'),
      (match) => '• ${match.group(1)}',
    );
    
    // Clean up multiple asterisks
    formatted = formatted.replaceAll(RegExp(r'\*+'), '');
    
    // Add proper spacing for sections
    formatted = formatted.replaceAllMapped(
      RegExp(r'(\d+\.\s+[^\n]+)'),
      (match) => '\n📋 ${match.group(1)}\n',
    );
    
    // Add emojis for better visual appeal
    formatted = formatted.replaceAll('Cuenta de Ahorro', '💰 Cuenta de Ahorro');
    formatted = formatted.replaceAll('Inversión a Plazo Fijo', '📈 Inversión a Plazo Fijo');
    formatted = formatted.replaceAll('Pagaré', '📄 Pagaré');
    formatted = formatted.replaceAll('Strategies', '🎯 Estrategias');
    formatted = formatted.replaceAll('Compare Rates', '🔍 Comparar Tasas');
    formatted = formatted.replaceAll('Within Hey Banco', '🏦 En Hey Banco');
    formatted = formatted.replaceAll('Against Competitors', '⚔️ Contra Competidores');
    formatted = formatted.replaceAll('Laddering', '🪜 Escalonamiento');
    
    // Clean up extra whitespace
    formatted = formatted.replaceAll(RegExp(r'\n\s*\n\s*\n'), '\n\n');
    formatted = formatted.trim();
    
    return formatted;
  }
}