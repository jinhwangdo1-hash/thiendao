package vn.thiendao.optimizer;
import android.os.Build;
import android.security.keystore.*;
import java.security.*;
import java.security.cert.Certificate;
import java.io.*;
import javax.security.auth.x500.X500Principal;
import io.github.muntashirakon.adb.*;
public class AdbBridge extends AbsAdbConnectionManager {
 private static AdbBridge instance;
 private final PrivateKey key;
 private final Certificate cert;
 public static synchronized AdbBridge get() throws Exception {if(instance==null)instance=new AdbBridge();return instance;}
 private AdbBridge() throws Exception {
 setApi(Build.VERSION.SDK_INT);
 KeyStore ks=KeyStore.getInstance("AndroidKeyStore");ks.load(null);
 String alias="optimizer-adb";
 if(!ks.containsAlias(alias)){KeyPairGenerator g=KeyPairGenerator.getInstance("RSA","AndroidKeyStore");g.initialize(new KeyGenParameterSpec.Builder(alias,KeyProperties.PURPOSE_SIGN|KeyProperties.PURPOSE_DECRYPT).setKeySize(2048).setDigests(KeyProperties.DIGEST_NONE,KeyProperties.DIGEST_SHA256,KeyProperties.DIGEST_SHA512,KeyProperties.DIGEST_SHA1).setSignaturePaddings(KeyProperties.SIGNATURE_PADDING_RSA_PKCS1).setEncryptionPaddings(KeyProperties.ENCRYPTION_PADDING_RSA_PKCS1).setCertificateSubject(new X500Principal("CN=Thien Dao Optimizer")).build());g.generateKeyPair();}
 key=(PrivateKey)ks.getKey(alias,null);cert=ks.getCertificate(alias);
 }
 protected PrivateKey getPrivateKey(){return key;}
 protected Certificate getCertificate(){return cert;}
 protected String getDeviceName(){return "Thien Dao Optimizer";}
 public synchronized String command(String cmd) throws Exception {try(AdbStream stream=openStream("shell:"+cmd);InputStream in=stream.openInputStream()){ByteArrayOutputStream out=new ByteArrayOutputStream();byte[] buf=new byte[4096];int n;while((n=in.read(buf))!=-1){out.write(buf,0,n);if(out.size()>65536)break;}return out.toString("UTF-8");}}
}