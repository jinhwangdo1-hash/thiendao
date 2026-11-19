package vn.thiendao.optimizer;
import android.os.Build;
import org.bouncycastle.cert.jcajce.*;
import org.bouncycastle.operator.jcajce.*;
import java.math.BigInteger;
import java.util.Date;
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
 KeyPairGenerator g=KeyPairGenerator.getInstance("RSA");g.initialize(2048);KeyPair pair=g.generateKeyPair();
 key=pair.getPrivate();
 X500Principal subject=new X500Principal("CN=Thien Dao Optimizer");
 long now=System.currentTimeMillis();
 JcaX509v3CertificateBuilder builder=new JcaX509v3CertificateBuilder(subject,new BigInteger(128,new SecureRandom()).add(BigInteger.ONE),new Date(now-86400000L),new Date(now+31536000000L),subject,pair.getPublic());
 cert=new JcaX509CertificateConverter().getCertificate(builder.build(new JcaContentSignerBuilder("SHA256withRSA").build(key)));
 }
 protected PrivateKey getPrivateKey(){return key;}
 protected Certificate getCertificate(){return cert;}
 protected String getDeviceName(){return "Thien Dao Optimizer";}
 public synchronized String command(String cmd) throws Exception {try(AdbStream stream=openStream("shell:"+cmd);InputStream in=stream.openInputStream()){ByteArrayOutputStream out=new ByteArrayOutputStream();byte[] buf=new byte[4096];int n;while((n=in.read(buf))!=-1){out.write(buf,0,n);if(out.size()>65536)break;}return out.toString("UTF-8");}}
}