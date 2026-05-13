-- MySQL dump 10.13  Distrib 8.0.44, for Win64 (x86_64)
--
-- Host: 127.0.0.1    Database: salao_cabeleireira
-- ------------------------------------------------------
-- Server version	8.0.44

/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!50503 SET NAMES utf8 */;
/*!40103 SET @OLD_TIME_ZONE=@@TIME_ZONE */;
/*!40103 SET TIME_ZONE='+00:00' */;
/*!40014 SET @OLD_UNIQUE_CHECKS=@@UNIQUE_CHECKS, UNIQUE_CHECKS=0 */;
/*!40014 SET @OLD_FOREIGN_KEY_CHECKS=@@FOREIGN_KEY_CHECKS, FOREIGN_KEY_CHECKS=0 */;
/*!40101 SET @OLD_SQL_MODE=@@SQL_MODE, SQL_MODE='NO_AUTO_VALUE_ON_ZERO' */;
/*!40111 SET @OLD_SQL_NOTES=@@SQL_NOTES, SQL_NOTES=0 */;

--
-- Table structure for table `agendamento_servicos`
--

DROP TABLE IF EXISTS `agendamento_servicos`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `agendamento_servicos` (
  `id` int NOT NULL AUTO_INCREMENT,
  `agendamento_id` int NOT NULL,
  `servico_id` int NOT NULL,
  PRIMARY KEY (`id`),
  KEY `agendamento_id` (`agendamento_id`),
  KEY `servico_id` (`servico_id`),
  CONSTRAINT `agendamento_servicos_ibfk_1` FOREIGN KEY (`agendamento_id`) REFERENCES `agendamentos` (`id`),
  CONSTRAINT `agendamento_servicos_ibfk_2` FOREIGN KEY (`servico_id`) REFERENCES `servicos` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=30 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `agendamento_servicos`
--

LOCK TABLES `agendamento_servicos` WRITE;
/*!40000 ALTER TABLE `agendamento_servicos` DISABLE KEYS */;
INSERT INTO `agendamento_servicos` VALUES (1,1,1),(4,6,1),(5,6,2),(6,7,5),(7,8,5),(8,9,5),(9,10,7),(10,11,7),(11,12,4),(12,13,4),(13,14,1),(22,23,1),(29,30,1);
/*!40000 ALTER TABLE `agendamento_servicos` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `agendamentos`
--

DROP TABLE IF EXISTS `agendamentos`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `agendamentos` (
  `id` int NOT NULL AUTO_INCREMENT,
  `usuario_id` int NOT NULL,
  `data_agendamento` date NOT NULL,
  `hora_agendamento` time NOT NULL,
  `status` enum('agendado','cancelado','concluido') DEFAULT 'agendado',
  `criado_em` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  KEY `usuario_id` (`usuario_id`),
  CONSTRAINT `agendamentos_ibfk_1` FOREIGN KEY (`usuario_id`) REFERENCES `usuarios` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=31 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `agendamentos`
--

LOCK TABLES `agendamentos` WRITE;
/*!40000 ALTER TABLE `agendamentos` DISABLE KEYS */;
INSERT INTO `agendamentos` VALUES (1,1,'2026-03-16','10:00:00','cancelado','2026-03-16 12:47:13'),(2,3,'2026-03-25','10:00:00','agendado','2026-03-22 20:40:34'),(3,4,'2026-03-27','14:00:00','agendado','2026-03-23 02:33:24'),(4,5,'2026-03-30','10:00:00','agendado','2026-03-23 02:47:44'),(5,6,'2026-03-25','15:00:00','agendado','2026-03-23 03:02:52'),(6,5,'2026-03-27','14:00:00','agendado','2026-03-23 03:25:30'),(7,7,'2026-03-25','14:30:00','agendado','2026-03-23 04:15:05'),(8,8,'2026-03-27','15:30:00','agendado','2026-03-23 13:46:30'),(9,5,'2026-03-25','16:30:00','agendado','2026-03-23 13:59:30'),(10,5,'2026-03-30','13:00:00','agendado','2026-03-23 14:47:40'),(11,5,'2026-03-31','13:00:00','agendado','2026-03-23 14:48:42'),(12,9,'2026-04-10','09:30:00','agendado','2026-03-24 14:24:57'),(13,10,'2026-03-25','10:30:00','agendado','2026-03-24 15:16:03'),(14,11,'2026-05-03','14:30:00','agendado','2026-05-03 16:39:43'),(23,20,'2026-05-04','09:30:00','concluido','2026-05-03 23:14:33'),(30,17,'2026-05-10','12:00:00','agendado','2026-05-10 01:31:49');
/*!40000 ALTER TABLE `agendamentos` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `pagamentos`
--

DROP TABLE IF EXISTS `pagamentos`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `pagamentos` (
  `id` int NOT NULL AUTO_INCREMENT,
  `agendamento_id` int NOT NULL,
  `valor` decimal(8,2) NOT NULL,
  `forma_pagamento` enum('dinheiro','pix','cartao') NOT NULL,
  `data_pagamento` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  KEY `agendamento_id` (`agendamento_id`),
  CONSTRAINT `pagamentos_ibfk_1` FOREIGN KEY (`agendamento_id`) REFERENCES `agendamentos` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `pagamentos`
--

LOCK TABLES `pagamentos` WRITE;
/*!40000 ALTER TABLE `pagamentos` DISABLE KEYS */;
/*!40000 ALTER TABLE `pagamentos` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `servicos`
--

DROP TABLE IF EXISTS `servicos`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `servicos` (
  `id` int NOT NULL AUTO_INCREMENT,
  `nome` varchar(100) NOT NULL,
  `descricao` text,
  `preco` decimal(8,2) NOT NULL,
  `duracao_minutos` int NOT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=23 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `servicos`
--

LOCK TABLES `servicos` WRITE;
/*!40000 ALTER TABLE `servicos` DISABLE KEYS */;
INSERT INTO `servicos` VALUES (1,'Corte Feminino','Corte de cabelo Feminino',60.00,40),(2,'Escova','Escova simples',35.00,30),(3,'Hidratacao','Tratamento de Hidratacao capilar',60.00,120),(4,'Progressiva','Alisamento progressivo',180.00,180),(5,'Pintura','Coloracao completa do cabelo',150.00,120),(6,'Reconstrução Capilar','Tratamento profundo para recuperar fios danificados',120.00,60),(7,'Nutrição Capilar','Reposição de nutrientes para cabelo ressecado',80.00,50),(8,'Cauterização','Selagem das cutículas do cabelo com queratina',150.00,90),(9,'Reconstrução Capilar','Tratamento profundo para recuperar fios danificados',120.00,60),(10,'Nutrição Capilar','Reposição de nutrientes para cabelo ressecado',80.00,50),(11,'Cauterização','Selagem das cutículas do cabelo com queratina',150.00,90),(12,'Mechas','Clareamento parcial dos fios',180.00,120),(13,'Luzes','Iluminação do cabelo com técnica profissional',220.00,150),(14,'Balayage','Técnica moderna de coloração natural',250.00,180),(15,'Babyliss','Modelagem com cachos',70.00,40),(16,'Penteado para festa','Penteado elaborado para eventos',120.00,90),(17,'Lavagem + Secagem','Lavagem simples com finalização',30.00,20),(18,'Botox Capilar','Redução de volume e hidratação profunda',130.00,90),(19,'Selagem','Alinhamento dos fios com brilho',140.00,120),(20,'Relaxamento','Redução de volume para cabelos cacheados',180.00,120),(21,'Design de Sobrancelha','Modelagem de sobrancelhas',40.00,30),(22,'Maquiagem','Maquiagem profissional para eventos',130.00,60);
/*!40000 ALTER TABLE `servicos` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `usuarios`
--

DROP TABLE IF EXISTS `usuarios`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `usuarios` (
  `id` int NOT NULL AUTO_INCREMENT,
  `nome` varchar(100) NOT NULL,
  `email` varchar(120) NOT NULL,
  `senha` varchar(255) NOT NULL,
  `telefone` varchar(20) NOT NULL,
  `tipo` enum('cliente','funcionario','admin') DEFAULT 'cliente',
  `criado_em` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `email` (`email`)
) ENGINE=InnoDB AUTO_INCREMENT=23 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `usuarios`
--

LOCK TABLES `usuarios` WRITE;
/*!40000 ALTER TABLE `usuarios` DISABLE KEYS */;
INSERT INTO `usuarios` VALUES (2,'Anderson Gustavo','anderson@email.com','123456','159962222','funcionario','2026-03-16 12:35:55'),(13,'Admin','admin@email.com','123456','11999999999','admin','2026-05-03 17:16:47'),(15,'Andressa','Andressa@salao.com','123456','11999999999','admin','2026-05-03 17:46:45'),(17,'itala','cliente@email.com','123456','11977777777','cliente','2026-05-03 17:46:45'),(18,'Iago','iago@email.com','123456','11998877664','cliente','2026-05-03 21:22:50'),(20,'maria','maria@email.com','123456','1199887758','funcionario','2026-05-03 23:13:58');
/*!40000 ALTER TABLE `usuarios` ENABLE KEYS */;
UNLOCK TABLES;
/*!40103 SET TIME_ZONE=@OLD_TIME_ZONE */;

/*!40101 SET SQL_MODE=@OLD_SQL_MODE */;
/*!40014 SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS */;
/*!40014 SET UNIQUE_CHECKS=@OLD_UNIQUE_CHECKS */;
/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
/*!40111 SET SQL_NOTES=@OLD_SQL_NOTES */;

-- Dump completed on 2026-05-09 22:51:53
